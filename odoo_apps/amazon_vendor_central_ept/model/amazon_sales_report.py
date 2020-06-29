import base64
from io import StringIO
import csv
import logging
import time
from datetime import datetime
from tempfile import NamedTemporaryFile
from odoo import models, fields, api, _
from odoo.osv import osv

_logger = logging.getLogger(__name__)

class Amazon_Sales_Report(models.Model):
    _name = 'amazon.sales.report'

    name = fields.Char(string='Reference Number')
    sender_gln_id = fields.Char(string='Sender GLN Number')
    vendor_id = fields.Many2one('amazon.vendor.instance',string='Vendor')
    vendor_code = fields.Char(string='Vendor Code')
    issued_date = fields.Datetime(string='Document Issued Date')
    supplier_gln_id = fields.Char('Supplier GLN Number')
    currency_id = fields.Many2one('res.currency', string='Currency')
    amazon_sales_report_line_ids = fields.One2many('amazon.sales.report.line', 'amazon_sales_report_id',
                                                   string='Amazon Sales Report Lines')
    message_ref_number = fields.Char(string='Message Reference Number')

    @api.multi
    def sync_import_sales_report(self, args = {}):
        """
        USE: this method called from auto import sale report cron job.
        :param args: in args{} vendor_id variable pass from cron.
        :return: Boolean
        """
        if not args.get('vendor_id'):
            raise osv.except_osv(_('Error'),_('No Vendor instance found..! Check cron job first.'))
        else:
            vendor_id = args.get('vendor_id')
        self.import_sales_report(vendor_id = vendor_id)
        return True

    @api.multi
    def import_sales_report(self,vendor_id=False):
        amazon_vendor_instance_obj = self.env['amazon.vendor.instance']
        self.instance_id = None
        if not vendor_id:
            raise osv.except_osv(_('Error'), _('No Vendor instance found..!'))
        else:
            self.instance_id = amazon_vendor_instance_obj.browse(vendor_id)

        file_to_delete = []
        connection_id = False
        if self.instance_id.sales_report_connection_type == 'test_connection':
            connection_id = self.instance_id.sales_report_test_ftp_id
        elif self.instance_id.sales_report_connection_type == 'production_connection':
            connection_id = self.instance_id.sales_report_production_ftp_id
        else:
            raise osv.except_osv(_('Error'), _(
                    'First of all select Connection detail.! \nAmazon Vendor Central >> Configuration >> Vendor >> Sales Report'))

        with self.instance_id.get_new_edi_reception_interface(connection_id) \
                as edi_interface:
            # `filenames` contains a list of filenames to be imported
            filenames_dict = edi_interface.pull_from_ftp('SLSRPT')

        for server_filename, filename in filenames_dict.items():
            self.export_avc_line_id = []
            with open(filename) as file:
                self.filename = filename
                self.server_filename = server_filename
                self.process_seles_report(file)
            file_to_delete.append(server_filename)

            if self.job_id:
                binary_package = open(filename).read()
                attachment_vals = {
                    'name':server_filename,
                    'datas':base64.encodestring(binary_package),
                    'datas_fname':server_filename,
                    'type':'binary',
                    'res_model':'avc.file.transaction.log',
                    'res_id':self.job_id.id,
                }
                attachment = self.env['ir.attachment'].create(attachment_vals)

                self.job_id.message_post(body=_("<b>Sales Report Import File</b>"), attachment_ids=attachment.ids)
                self.job_id.message_post(body=_(("<b>Sales Report created %s</b>" % (
                self.sales_report_id.name or '') if self.sales_report_id else "<b>Invalid supplier id</b>")))
        message = ''
        if file_to_delete:
            with self.instance_id.get_new_edi_reception_interface(connection_id) \
                    as edi_interface:
                # `filenames` contains a list of filenames to be imported
                edi_interface.sftp_client.chdir(edi_interface.download_dir)
                for filename in file_to_delete:
                    edi_interface.delete_from_ftp(filename)

            message = "Sales Report Successfully imported"
        else:
            message = "No file found..!"
        _logger.info(message)
        for lines in self.export_avc_line_id:
            lines.write({'filename':filename})
        self.job_id.write({'filename':filename})
        return True

    @api.multi
    def process_seles_report(self,file):
        """
        USE: here edi file converted and created a amazon.sales.report model's record
        :param file: A Sales Rerport file received from amazon vendor central
        :return: Boolean
        """
        #declaration
        amazon_seller_location_code_obj = self.env['amazon.seller.location.code']
        avc_file_process_job_obj = self.env['avc.file.transaction.log']
        res_currency_obj = self.env['res.currency']

        line_no = 0
        total_segment = 0
        sales_report_info={}
        sales_report_line_info = {}

        # read and seprate file in diffrent part
        for segment in csv.reader(file, delimiter="'", quotechar='|'):
            seller_location_id = report_end_date = report_start_date = None
            for seg in segment:
                if seg.startswith('UNB+UNOA') or seg.startswith('UNB+UNOC'):
                    header = seg.split("+")
                    if self.instance_id.supplier_id != header[3][:-3]:
                        raise osv.except_osv(_('Error'),_("File Recipient ID and Vendor's Supplier ID is not matched..!"))
                    sales_report_info.update({'sender_gln_id':header[2][:-3], 'vendor_id':self.instance_id.id})
                    total_segment += 1

                elif seg.startswith('UNH'):
                    total_segment += 1

                elif seg.startswith('BGM+'):
                    vendor_code = seg.split("+")
                    vendor_code = vendor_code[2][:-8]
                    sales_report_info.update({'vendor_code':vendor_code})
                    total_segment += 1

                elif seg.startswith('DTM+137'):
                    date_seg = seg.split(":")
                    issued_date = datetime.strptime(date_seg[1], '%Y%m%d')
                    sales_report_info.update({'issued_date':issued_date})
                    total_segment += 1

                elif seg.startswith('NAD+SE'):
                    seller_code = seg.split("+")[2][:-3]
                    total_segment += 1

                elif seg.startswith('NAD+SU'):
                    supplier_gln_id= seg.split("+")[2][:-3]
                    sales_report_info.update({'supplier_gln_id':supplier_gln_id or ''})
                    total_segment += 1

                elif seg.startswith('CUX+'):
                    currency = seg.split(":")
                    currency_id = res_currency_obj.search([('name','=',currency[1])])
                    sales_report_info.update({'currency_id':currency_id.id})
                    total_segment += 1

                elif seg.startswith('LOC+'):
                    location = seg.split("+")[2][:-3]
                    seller_location_id = amazon_seller_location_code_obj.search([('gln_number','=',location)])
                    total_segment +=1

                elif seg.startswith('DTM+90'):
                    date_seg = seg.split(":")
                    report_start_date = datetime.strptime(date_seg[1], '%Y%m%d')
                    total_segment += 1

                elif seg.startswith('DTM+91'):
                    date_seg = seg.split(":")
                    report_end_date = datetime.strptime(date_seg[1], '%Y%m%d')
                    total_segment += 1

                elif seg.startswith('LIN+'):
                    line_no += 1
                    sales_report_line_info.update({'Line_' + str(line_no):{'report_start_date':report_start_date,
                                                                           'report_end_date':report_end_date,
                                                                           'seller_location_id':seller_location_id.id or False}})
                    ean = seg.split("+")
                    ean = ean[len(ean) - 1]
                    if ean.upper().find('EN', 0, len(ean)) != -1 and ean.upper().find(':', 0, len(ean)) != -1:
                        ean = ean.split(":") and ean.split(":")[0] or ''
                        sales_report_line_info['Line_' + str(line_no)].update({'ean':ean})
                    # UP used for Universal Product Code **code edited here**
                    elif ean.upper().find('UP', 0, len(ean)) != -1 and ean.upper().find(':', 0, len(ean)) != -1:
                        ean = ean.split(":") and ean.split(":")[0] or ''
                        sales_report_line_info['Line_' + str(line_no)].update({'ean':ean})
                    total_segment += 1

                elif seg.startswith('PIA+'):
                    code = seg.split("+")
                    code = code[2][:-3] if len(code)>2 else ''
                    sales_report_line_info['Line_'+str(line_no)].update({'default_code':code})
                    total_segment +=1

                elif seg.startswith('MOA+36E'):
                    cost_of_goods_sold = seg.split(":")[1]
                    sales_report_line_info['Line_' + str(line_no)].update({'cost_of_goods_sold':float(cost_of_goods_sold)})
                    total_segment += 1

                elif seg.startswith('QTY+153'):
                    sold_qty = seg.split(":")[1]
                    sales_report_line_info['Line_' + str(line_no)].update({'sold_qty':float(sold_qty)})
                    total_segment += 1

                elif seg.startswith('QTY+145'):
                    qty_on_hand = seg.split(":")[1]
                    sales_report_line_info['Line_' + str(line_no)].update({'qty_on_hand':float(qty_on_hand)})
                    total_segment += 1

                elif seg.startswith('QTY+21'):
                    ordered_qty = seg.split(":")[1]
                    sales_report_line_info['Line_' + str(line_no)].update({'ordered_qty':float(ordered_qty)})
                    total_segment += 1

                elif seg.startswith('UNT+'):
                    segments = seg.split("+")
                    if int(segments[1]) != total_segment:
                        raise osv.except_osv(_('Error'), _('File not integrated properly, Please Check file data.'))
                    sales_report_info.update({'name':segments[2]})

                elif seg.startswith('UNZ+'):
                    interchange = seg.split("+")
                    sales_report_info.update({'message_ref_number':interchange[2]})
            #print str(sales_report_info) + '\n' + str(sales_report_line_info)
            self.sales_report_id = self.create(sales_report_info)

            # CREATE LOG IN avc.file.transaction.log
            avc_file_process_job_vals = {
                'message':'Sales Report imported',
                'filename':self.server_filename,
                'vendor_id':self.instance_id.id,
                'application':'sales_report',
                'operation_type':'import',
                'create_date':datetime.now(),
                'company_id':self.instance_id.company_id.id or False,
            }
            self.job_id = avc_file_process_job_obj.create(avc_file_process_job_vals)

            self.create_sales_report_line_info(sales_report_line_info = sales_report_line_info, sales_report_id = self.sales_report_id)
        return True
    @api.multi
    def create_sales_report_line_info(self,sales_report_line_info = False, sales_report_id = False):
        """
        USE: To create sales report line
        :param sales_report_line_info: received sales report lines dict from amazon vendor central.
        :param sales_report_id: amazon.sales.report browseble object
        :return: Boolean
        """
        if not sales_report_line_info or not sales_report_id:
            raise osv.except_osv(_('Error'),_('Required information not found for create sales report line..!'))

        product_obj = self.env['product.product']
        message = ''
        remark = ''
        for key, value in sales_report_line_info.iteritems():
            line_vals = {'amazon_sales_report_id':sales_report_id.id}
            domain = []
            if value.get('ean',''):
                domain.append(('barcode','=',value.get('ean','')))
            elif value.get('default_code',''):
                domain.append(('default_code','=',value.get('default_code', '')))
            product_id = product_obj.search(domain)
            if not product_id:
                message = 'Product not found'
                if value.get('ean', ''):
                    remark = 'barcode:%s'%(value.get('ean', ''))
                if not value.get('ean', '') and value.get('default_code', ''):
                    remark = 'default_code:%s' % (value.get('default_code', ''))
            else:
                line_vals.update({'product_id':product_id.id,
                                  'cost_of_goods_sold':float(value.get('cost_of_goods_sold',0)),
                            'sold_qty':float(value.get('sold_qty',0)),
                            'qty_on_hand':float(value.get('qty_on_hand',0)),
                            'ordered_qty':float(value.get('ordered_qty',0)),
                            'seller_location_id':value.get('seller_location_id',False),
                            'report_end_date':value.get('report_end_date', False),
                            'report_start_date':value.get('report_start_date', False)
                            })
            line_id = self.amazon_sales_report_line_ids.create(line_vals)
            # CREATE LOG IN avc.transaction.log.line
            avc_transaction_log_val = {
                'message': message if message else 'Sales Report line imported',
                'remark': remark if remark else 'Sales Report name %s' % (sales_report_id.name or ''),
                'job_id':self.job_id.id,
                'product_id':product_id.id or False,
                'company_id':self.job_id.company_id.id or False,
                'user_id':self.env.user.id,
                'application':'sales_report',
                'processed_qty':value.get('qty_on_hand','0'),
                'create_date':datetime.now(),
                'operation_type':'import',
                'is_mismatch':False if product_id else True,
            }
            res = self.job_id.transaction_log_ids.create(avc_transaction_log_val)
            self.export_avc_line_id.append(res)
        return True