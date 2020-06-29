from odoo import models,fields,api,_
from odoo.osv import expression,osv
from odoo.exceptions import Warning
from ftplib import FTP
from tempfile import NamedTemporaryFile
from . amazon_edi_interface import AmazonEDIInterface
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
#import paramiko
import base64
import csv
import logging
_logger = logging.getLogger(__name__)

class Account_Invoice(models.Model):
    _inherit = 'account.invoice'
    
    is_amazon_edi_invoice = fields.Boolean(string = 'Is Amazon EDI Invoice', compute="_get_is_amazon_edi_invoice")
    exported_to_edi = fields.Boolean(string = 'Invoice Exported to Amazon EDI')

    @api.multi
    def _get_is_amazon_edi_invoice(self):
        sale_order_obj = self.env['sale.order']
        for line in self:
            query = """select order_id 
                        from sale_order_line 
                        where id in 
                          (select order_line_id 
                          from sale_order_line_invoice_rel 
                          where invoice_line_id in 
                            (select id 
                            from account_invoice_line 
                            where invoice_id = %s))""" % (line.id)
            self.env.cr.execute(query)
            sale_order_ids = []
            for record in self.env.cr.dictfetchall():
                if not record['order_id'] in sale_order_ids:
                    sale_order_ids.append(record['order_id'])
            sale_order_ids = sale_order_obj.browse(sale_order_ids)
            if sale_order_ids:
                line.is_amazon_edi_invoice = sale_order_ids[0].is_amazon_edi_order

    @api.multi
    def prepare_and_send_edi_order_invoice_message(self,args={}):
        sale_order_obj = self.env['sale.order']
        avc_file_process_job_obj = self.env['avc.file.transaction.log']
        account_invoice_tax_obj = self.env['account.invoice.tax']
        if not args.get('vendor_id'):
            sale_order_ids = sale_order_obj.search([('name','=',self.origin),('is_amazon_edi_order','=',True)])
        else:
            vendor_id = args.get('vendor_id')
            sale_order_ids = sale_order_obj.search([('is_amazon_edi_order','=',True),('invoice_count','>',0),('vendor_id','=',vendor_id)])
        for order in sale_order_ids:
            self.job_id = None
            invoice_ids = order.mapped('invoice_ids')
            stock_picking_ids = order.mapped('picking_ids')
            for invoice in invoice_ids:
                transaction_line_ids=[]
                invoice.write({'is_amazon_edi_invoice':True})
                if invoice.state in ['draft','cancel'] or invoice.exported_to_edi == True:
                    continue
                count=0
                for lines in invoice.invoice_line_ids:
                    if lines.product_id.type != 'service':
                       count +=1
                if count == 0:
                    continue
                #NOTE: here taken 1st stock picking record based on thate record date of delivery set.
                date_deliver = stock_picking_ids[0].date_done
                if not date_deliver:
                    raise osv.except_osv(_('Error'),
                                         _("No delivery date found..!\nCheck %s's stock picking..! " % (order.name)))
                else:
                    date_deliver = datetime.strptime(date_deliver, '%Y-%m-%d %H:%M:%S')
                    date_deliver = date_deliver.strftime("%Y%m%d")

                #NOTE: here TAX RATE taken from account.invoice.tax where invoice_id is current record's invoice_id and first record's data are considered
                account_invoice_tax_id = account_invoice_tax_obj.search([('invoice_id','=',invoice.id)], limit = 1)
                invoice_tax_rate = account_invoice_tax_id.tax_id.amount or 0.0
                if not self.job_id:
                    avc_file_process_job_values = {
                        'message': 'Invoice exported',
                        'vendor_id': order.vendor_id.id,
                        'application' : 'invoice',
                        'operation_type' : 'export',
                        'create_date' : datetime.now(),
                        'company_id':order.company_id.id,
                        'sale_order_id':order.id,
                        }
                    self.job_id = avc_file_process_job_obj.create(avc_file_process_job_values)
                
                order_name = order.amazon_edi_order_id
                message_id = order.amazon_edi_message_info_id
                if not message_id:
                    raise osv.except_osv(_('Error'), _('Message information is not found in sale order %s, so we should not send invoice to Amazon EDI.'%(order.name)))
                if not message_id.sender_id or not message_id.recipient_id:
                    raise osv.except_osv(_('Error'), _('Sender or recipient identifier not found.'))
                invoice_seq = self.env['ir.sequence'].get('amazon.edi.invoice.message.number')
                total_segment = 0
                file_invoice = NamedTemporaryFile(delete=False)
                file_invoice.write("""UNB+UNOA:2+%s:%s+%s:%s+%s:%s+%s+++++EANCOM'"""%(message_id.recipient_id or '',order.vendor_id.vendor_qualifier,message_id.sender_id or '',order.vendor_id.amazon_qualifier,time.strftime("%y%m%d"),time.strftime("%H%M"),str(invoice_seq)))
                total_segment +=1
                file_invoice.write("""UNH+1+INVOIC:D:96A:UN:EAN008'""")
                total_segment +=1
                inv_no = invoice.number and invoice.number[invoice.number.rfind('/')+1:] or ''
                file_invoice.write("""BGM+380+%s'"""%(str(inv_no)))
                total_segment +=1
                file_invoice.write("""DTM+137:%s:102'"""%(time.strftime("%Y%m%d")))
                total_segment +=1
                file_invoice.write("""DTM+35:%s:102'"""%(date_deliver))
                total_segment +=1
                #Supplier Segment
                company_name = invoice.company_id and (invoice.company_id.name).replace("'","") or 'MGC International'
                company_street = invoice.company_id and (invoice.company_id.street).replace("'","") or ("10 passage de l'industrie").replace("'","")
                company_city = invoice.company_id and (invoice.company_id.city).replace("'","") or "Paris"
                company_zip = invoice.company_id and (invoice.company_id.zip).replace("'","") or "75010"
                country_code = invoice.company_id and invoice.company_id.country_id and invoice.company_id.country_id.code or "FR"  
                vat_reg_no = invoice.company_id and invoice.company_id.vat or 'FR60323552828' # MGC(Supplier) VAT Number
                file_invoice.write("""NAD+SU+%s::9++%s+%s+%s++%s+%s'"""%(str(message_id.supplier_id),company_name,company_street,company_city,str(company_zip),country_code))
                total_segment +=1
                file_invoice.write("""RFF+VA:%s'""" % (vat_reg_no))
                total_segment += 1
                file_invoice.write("""NAD+DP+%s::9+++++++%s'""" % (message_id.buyer_id, message_id.country_code))
                total_segment += 1
                #Invoice Segment
                iv_name = invoice.partner_id and (invoice.partner_id.name).replace("'","") or ''
                street = invoice.partner_id and (invoice.partner_id.street).replace("'","") or ''
                street2 = invoice.partner_id and (invoice.partner_id.street2).replace("'","") or ''
                city = invoice.partner_id and (invoice.partner_id.city).replace("'","") or ''
                zipcode = invoice.partner_id and invoice.partner_id.zip or ''
                country_code = invoice.partner_id and invoice.partner_id.country_id and invoice.partner_id.country_id.code or 'FR'  
                file_invoice.write("""NAD+IV+%s::9++%s:%s+%s+%s++%s+%s'"""%(message_id.invoice_id,iv_name,street,street2,city,zipcode,country_code))
                total_segment +=1
                file_invoice.write("""RFF+VA:%s'""" % (message_id.vat_number or ''))
                total_segment += 1
                file_invoice.write("""CUX+2:%s:4'"""%(message_id.currancy_code or 'EUR'))
                total_segment +=1
                file_invoice.write("""PAT+1++5::D:30'""") #payment Term 30 days Net
                total_segment +=1
                date_done = datetime.strptime(order.date_order, '%Y-%m-%d %H:%M:%S')
                date_done = date_done.strftime("%Y%m%d")
                file_invoice.write("""DTM+171:%s:102'"""%(date_done)) #payment Term 30 days Net
                total_segment +=1

                line_no = 1
                tax_per = 0.0
                for line in invoice.invoice_line_ids:
                    if line.product_id.type == 'service':
                        continue
                    code = line.product_id and line.product_id.default_code or ''
                    ean = line.product_id  and line.product_id.barcode or ''
                    qty = line.quantity or 0.0
                    subtotal = line.price_subtotal 
                    price = line.price_unit
                    tax_per = line.invoice_line_tax_ids and line.invoice_line_tax_ids[0] and (line.invoice_line_tax_ids[0].amount) or 0
                    tax_amount = (price * tax_per) / 100
                    tax_amount = "%.2f" % tax_amount
                    if ean:
                        file_invoice.write("""LIN+%s++%s:EN'"""%(str(line_no),ean))
                        total_segment +=1
                    else:
                        file_invoice.write("""LIN+%s'""" % (str(line_no)))
                        total_segment += 1
                        file_invoice.write("""PIA+5+%s:SA'"""%(str(code)))
                        total_segment +=1
                    file_invoice.write("""QTY+47:%s'"""%(str(qty)))
                    total_segment +=1
                    file_invoice.write("""MOA+203:%s:%s:4'"""%(str(subtotal), invoice.currency_id.name or 'EUR')) #Line item amount
                    total_segment +=1
                    file_invoice.write("""PRI+AAA:%s:CT:NTP'"""%(str(price))) #Net Price Unit
                    total_segment +=1
                    file_invoice.write("""RFF+ON:%s'"""%(str(order_name))) #Order Name
                    total_segment +=1
                    file_invoice.write("""TAX+7+VAT+++:::%s'"""%(str(int(tax_per))))
                    total_segment +=1
                    file_invoice.write("""MOA+124:%s:%s:4'""" % (str(tax_amount), invoice.currency_id.name or 'EUR'))
                    total_segment += 1
                    line_no +=1
                    
                    avc_transaction_log_val = {
                        'message':'Invoice Line Created',
                        'remark':'sale order id %s'%(order.id),
                        'sale_order_id':order.id,
                        'job_id':self.job_id.id,
                        'picking_id':stock_picking_ids[0].id or False,
                        'back_order_id':False,
                        'product_id':line.product_id.id,
                        'package_id':False,
                        'stock_inventory_id':False,
                        'company_id':order.company_id.id,
                        'user_id':self.env.user.id,
                        'picking_state':stock_picking_ids[0].state,
                        'application':'invoice',
                        'export_qty':qty,
                        'processed_qty':qty,
                        'create_date':datetime.now(),
                        'operation_type':'export',
                        }
                    line_id = self.job_id.transaction_log_ids.create(avc_transaction_log_val)
                    transaction_line_ids.append(line_id)
                    
                file_invoice.write("""UNS+S'""")
                total_segment +=1    
                file_invoice.write("""CNT+2:%s'"""%(str(line_no-1)))
                total_segment +=1
                file_invoice.write("""MOA+77:%s:%s:4'"""%(str(invoice.amount_total),str(message_id.currancy_code))) #Whole Invoice Amount total with tax included
                total_segment +=1
                file_invoice.write("""TAX+7+VAT+++:::%s'"""%(str(int(invoice_tax_rate)))) # Whole invoice Tax Rate
                total_segment +=1
                file_invoice.write("""MOA+124:%s:%s:4'"""%(str(invoice.amount_tax),str(message_id.currancy_code))) #Tax Amount
                total_segment +=1
                file_invoice.write("""MOA+125:%s:%s:4'"""%(str(invoice.amount_untaxed),str(message_id.currancy_code))) #Untaxed Amount
                total_segment +=1
                    
                file_invoice.write("""UNT+%s+1'"""%(str(total_segment)))
                file_invoice.write("""UNZ+1+%s'"""%(str(invoice_seq)))
    
                file_invoice.close()
        
                fl = file(file_invoice.name, 'rb')
                out = base64.encodestring(fl.read())
        
                filename = "ORDINVOIC_%s.txt" %(str(order_name))
                
                upload_file_name = '%s_%s_%s_%s_%s_%s_%s.mgc'%(filename,datetime.now().day,datetime.now().month,datetime.now().year,datetime.now().hour,datetime.now().minute,datetime.now().second)
                vals = {
                    'name':upload_file_name,
                    'datas':out,
                    'datas_fname':upload_file_name,
                    'res_model':'avc.file.transaction.log',
                    'type':'binary',
                    'res_id':self.job_id.id,
                    }
                
                attachment = self.env['ir.attachment'].create(vals)     
                self.job_id.message_post(body=_("<b>Invoice EDI file</b>"),attachment_ids=attachment.ids)
                fl.close()
                connection_id = False
                if order.vendor_id.invoice_connection_type == 'test_connection':
                    connection_id = order.vendor_id.invoice_test_ftp_id
                elif order.vendor_id.invoice_connection_type == 'production_connection':
                    connection_id = order.vendor_id.invoice_production_ftp_id
                else:
                    raise osv.except_osv(_('Error'), _(
                        'First of all select Connection detail.! \nAmazon Vendor Central >> Configuration >> Vendor >> Invoice'))
                with order.vendor_id.get_new_edi_sending_interface(connection_id) \
                            as edi_interface:
                    edi_interface.push_to_ftp(filename, file_invoice.name)
                
                self.job_id.write({'filename':upload_file_name})
                for lines in transaction_line_ids:
                    lines.write({'filename':upload_file_name})
                invoice.write({'exported_to_edi':True})
        return True
    