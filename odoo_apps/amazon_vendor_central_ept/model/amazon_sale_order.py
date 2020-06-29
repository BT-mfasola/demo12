# -*- coding: utf-8 -*-

import base64
from io import StringIO
import csv
import logging
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from tempfile import NamedTemporaryFile
from odoo import models, fields, api, _
from odoo.osv import osv
#from pdf417gen import encode, render_image
_logger = logging.getLogger(__name__)

class sale_order(models.Model):
    _inherit = "sale.order"
    
    @api.depends('avc_import_transaction_log_ids.skip_line')
    @api.multi
    def _is_order_is_mismatch(self):
        for order in self:
            for transaction_line in order.avc_import_transaction_log_ids :
                if transaction_line.skip_line:
                    order.is_mismatch_order = True

    is_amazon_edi_order  = fields.Boolean('is Amazon Order')
    amazon_edi_order_id = fields.Char('Amazon Order ID')
    amazon_order_ack_uploaded = fields.Boolean('Amazon order Acknowledgement Uploaded')
    amazon_order_dispatch_advice_uploaded = fields.Boolean('Amazon order Dispatch Advice uploaded')
    avc_import_transaction_log_ids = fields.One2many('avc.transaction.log.line','sale_order_id', string = 'AVC Import Transaction Log',domain=[('operation_type','=','import'),('application','=','sale_order')])
    avc_export_transaction_log_ids = fields.One2many('avc.transaction.log.line','sale_order_id', string = 'AVC Export Transaction Log',domain=[('operation_type','=','export'),('application','=','sale_order_response')])
    vendor_id = fields.Many2one('amazon.vendor.instance', string = "Vendor")
    requested_for_routing = fields.Boolean(string = "Requested for Routing")
    received_routing_info = fields.Boolean(string = "Received Routing Information")
    bill_of_lading_number = fields.Char(string = "Bill of Lading Number")
    account_type = fields.Char(string = "Account Type")
    is_mismatch_order = fields.Boolean('Is Mismatch Order',compute='_is_order_is_mismatch')
    mismatch_product = fields.Selection([('cancel', 'Cancel'), ('reject', 'Reject'), ('backorder', 'Backorder'), ],
                                        string='If Product not Found')
    
    # Messing Info details 
    
    sender_id = fields.Char('Sender ID',readonly=True)
    recipient_id = fields.Char('Recipient ID',readonly=True)
    message_type = fields.Char('Type',readonly=True)
    msg_version = fields.Char('Version',readonly=True)
    buyer_id = fields.Char('Buyer ID',readonly=True)
    buyer_address = fields.Char('Buyer Address',readonly=True)
    supplier_id = fields.Char('Supplier ID',readonly=True)
    delivery_party_id = fields.Char('Delivery Party ID',readonly=True)
    country_code = fields.Char('Delivery Country',readonly=True)
    invoice_id = fields.Char('Invoice Party ID',readonly=True)
    currancy_code = fields.Char('Currency Code',readonly=True)
    order_id = fields.Char('Sale Order ID',readonly=True) 
    vat_number = fields.Char('VAT Registration Number',readonly=True)
    max_delivery_date_ept = fields.Date(string = 'Max Delivery Date')
    delivery_date_ept = fields.Date(string='Delivery Date')
    
    @api.multi
    def action_confirm(self):
        res = super(sale_order,self).action_confirm()
        for order in self:
            if order.is_amazon_edi_order:
                for picking in order.picking_ids:
                    carrier_type = order.vendor_id and order.vendor_id.delivery_type
                    picking.write({'carrier_type' : carrier_type , 'vendor_id' : order.vendor_id.id})
    
    @api.multi
    def reimport_amazon_po_file(self):
        sale_order_line_obj = self.env['sale.order.line']
        product_obj = self.env['product.product']
        job_id = self.env['avc.file.transaction.log'].search([('sale_order_id','=',self.id)])
        if job_id :
            data = job_id.attachment_id and job_id.attachment_id.datas
            file = StringIO(base64.decodestring(data).decode())
            reader = csv.reader(file,delimiter="'",quotechar='|')
            order_line_info = {}
            line_no = 1
            for segment in reader:
                for seg  in segment:
                    if seg.startswith('LIN+'):
                        order_line_info.update({'Line_'+str(line_no):{}})
                        ean = seg.split("+")
                        ean = ean[len(ean)-1] 
                        if ean.upper().find('EN',0,len(ean)) !=-1 and ean.upper().find(':',0,len(ean)) !=-1:
                            ean = ean.split(":") and ean.split(":")[0] or ''
                            order_line_info['Line_'+str(line_no)].update({'ean':ean})
                        #UP used for Universal Product Code **code edited here**
                        elif ean.upper().find('UP',0,len(ean)) !=-1 and ean.upper().find(':',0,len(ean)) !=-1:
                            ean = ean.split(":") and ean.split(":")[0] or ''
                            order_line_info['Line_'+str(line_no)].update({'ean':ean})
                        line_no += 1
                        
                    elif seg.startswith('PIA+'):
                        code = seg.split("+") 
                        code = code[2][:-3] if len(code)>2 else ''
                        if not order_line_info['Line_'+str(line_no-1)].get('ean',False):
                            order_line_info['Line_'+str(line_no-1)].update({'default_code':code})
                        
                        
                    elif seg.startswith('QTY+'):
                        qty = seg.split(":") 
                        qty = qty[1] if len(qty)>1 else 0
                        order_line_info['Line_'+str(line_no-1)].update({'qty':qty})
                        
                    elif seg.startswith('PRI+'):
                        price = seg.split(":") 
                        price = price[1] if len(price)>1 else 0
                        order_line_info['Line_'+str(line_no-1)].update({'price':price})
            
            for key,value in order_line_info.items():
                amazon_code = value.get('default_code') or value.get('ean')
                sale_order_line = sale_order_line_obj.search([('amazon_edi_line_code','=',amazon_code),('order_id','=',self.id)])
                if not sale_order_line:
                    product = product_obj.search([('amazon_sku','=',amazon_code)])
                    if not product:
                        product = product_obj.search([('default_code','=',amazon_code)])
                        amazon_edi_code = 'SKU'
                    if not product :
                        product = product_obj.search([('barcode','=',amazon_code)])
                        amazon_edi_code = 'barcode'
                    if product:
                        qty = value.get('qty',0.0)
                        price = value.get('price',0.0) 
                        line=(product,price,amazon_code,qty)
                        orderlinevals,product_id, qty_code = self.prepare_order_line_vals(line,self)
                        if orderlinevals:
                            sale_order_line = sale_order_line_obj.create(orderlinevals)
                            remark = amazon_edi_code + ':' + amazon_code
                            transaction_line = self.env['avc.transaction.log.line'].search([('job_id','=',job_id.id),('remark','=',remark),('operation_type','=','import')])
                            if transaction_line:
                                vals = {
                                    'message':'Sale Order Line Created',
                                    'remark':'sale order id %s'%(self.name or ''),
                                    'sale_order_id':self.id,
                                    'job_id':job_id.id,
                                    'picking_id':False,
                                    'back_order_id':False,
                                    'sale_order_line_id':sale_order_line.id,
                                    'product_id':orderlinevals.get('product_id',''),
                                    'package_id':False,
                                    'stock_inventory_id':False,
                                    'company_id':job_id.company_id.id or False,
                                    'user_id':self.env.user.id,
                                    'picking_state':'draft',
                                    'application':'sale_order',
                                    'export_qty':orderlinevals.get('product_uom_qty',''),
                                    'processed_qty':orderlinevals.get('product_uom_qty',''),
                                    'manually_processed':False,
                                    'is_mismatch_detail':False,
                                    'skip_line':False,
                                    'skip_order':False,
                                    'filename':job_id.attachment_id.name,
                                    'create_date':datetime.now(),
                                    'operation_type':'import',
                                    'price':price,
                                    }
                                transaction_line.write(vals)
                        
                        
        return True
    
    @api.multi
    def export_dispatch_advice(self):
        """
        Use: To send Dispatch Advice to Amazon Vendor Central via EDI 856 file. Call manually from Sale Order Form view
        :return: Boolean
        """
        self.sync_export_dispatch_advice(sale_order_ids = self)
        return True
    
    @api.model
    def sync_import_amazon_edi_order(self,args={},file_datas=None, ):
        """
        Use : For import EDI 850 Purchase Order file
        This method call by cron,
        :param args: arguments pass by cron (vendor_id)
        :param file_datas: If Purchase Order create manualy then here you can send file.
        :return: Boolean
        """
        if not args.get('vendor_id'):
            vendor_id = self.env['ir.values'].get_default('avc.config.settings', 'vendor_id')
        else:
            vendor_id = args.get('vendor_id')
            print ("cron run vendor id : %s"%(vendor_id))
        vendor_obj = self.env['amazon.vendor.instance'].browse(vendor_id)
        self.import_sales_from_amazon_edi(vendor_obj,file_data=file_datas )
        return True
    
    @api.multi
    def import_sales_from_amazon_edi(self, vendor_ids = None,file_data=None):
        """
        Use: Fetch the sale orders file from FTP location,
            format the data into format required by Odoo
            and create the sale in Odoo
        :param vendor_id: Amazon Vendor Central Instance ID
        :param file_data: EDI 850 Purchase Order file
        :return: Boolean
        """
        ctx = self._context.copy() or {}
        
        for vendor in vendor_ids:
            self.job_id = None
            self.filename = None
            self.server_filename = None
            self.export_avc_line_id = []
            self.ack_error_lines=[]
            
            filenames_dict ={}
            if file_data:
                imp_file = StringIO(base64.decodestring(file_data))
                file_write = open('/tmp/order_data.txt','wb')
                file_write.writelines(imp_file.getvalue())
                file_write.close()
                file_read = open('/tmp/order_data.txt', "rU")
                dialect = csv.Sniffer().sniff(file_read.readline())
                file_read.seek(0)
                reader = csv.reader(file_read,delimiter="'",quotechar='|')
                file_read.seek(0)
                self.process_file_and_prapare_order(file_read)
            else:
                file_to_delete = []
                connection_id = False
                if vendor.is_production_environment:
                    ftp_server_id = vendor.production_ftp_connection
                    directory_id = vendor.production_po_directory_id
                else :
                    ftp_server_id = vendor.test_ftp_connection
                    directory_id = vendor.test_po_directory_id
                                                  
                with vendor.get_edi_receive_interface(ftp_server_id,directory_id) \
                            as edi_interface:
                    # `filenames` contains a list of filenames to be imported 
                    filenames_dict = edi_interface.pull_from_ftp(vendor.po_file_import_prefix) 
                            
                for server_filename, filename in filenames_dict.items():
                    
                    with open(filename) as file:
                        self.job_id = None
                        self.filename = filename
                        self.server_filename = server_filename
                        ctx.update({'filename':server_filename})
                        self.process_file_and_prapare_order(vendor,file)
                    file_to_delete.append(server_filename) #  : Ekta
                    
                    if self.job_id:
                        binary_package = open(filename).read().encode()
                        attachment_vals = {
                            'name':server_filename,
                            'datas':base64.encodestring(binary_package),
                            'datas_fname':server_filename,
                            'type':'binary',
                            'res_model': 'avc.file.transaction.log',
                            'res_id':self.job_id.id,
                            }
                        
                        attachment=self.env['ir.attachment'].create(attachment_vals)
                        self.job_id.write({'attachment_id' : attachment.id})
                        self.job_id.message_post(body=_("<b>PO Import File</b>"),attachment_ids=attachment.ids)
                        self.job_id.message_post(body=_(("<b>Sale Order created %s</b>"%(self.order_id.name or '') if self.order_id else "<b>Information Mismatch</b>")))
                        if vendor.auto_confirm_sale_order and vendor.auto_generate_po_ack and self.order_id:
                            self.auto_send_poa(sale_order_id = self.order_id)

                if file_to_delete:
                    with vendor.get_edi_receive_interface(ftp_server_id,directory_id) \
                                as edi_interface:
                        edi_interface.sftp_client.chdir(edi_interface.download_dir)
                        for filename in file_to_delete:
                            edi_interface.delete_from_ftp(filename)
        return True

    @api.multi
    def auto_send_poa(self,sale_order_id = None):
        """
        USE: This method will call export_po_ack() of stock.picking,
        :param sale_order_id:
        :return: stock.picking's export_po_ack()
        """
        if self.instance_id.auto_confirm_sale_order:
            res = sale_order_id.action_confirm()
            if res:
                picking_id = sale_order_id.mapped('picking_ids')
                if picking_id:
                    return picking_id[0].export_po_ack()
        else:
            message = "First of all set Sale Order Auto Confirm as True from Amazon Vendor Central >> Configuration >> Vendor >> Purchase Order Acknowledgement."
            _logger.info(message)
            raise osv.except_osv(_('Purchase Order Auto Acknowledgement send error'),_(message))

    @api.multi
    def process_file_and_prapare_order(self,vendor,file):
        """
        Use: Decode Amazon EDI 850 Purchase Order file and create sale order, sale order lines and required log entries.
        :param file: EDI 850 Purchase Order file
        :return: Boolean
        """
        #declaration
        country_obj = self.env['res.country']
        partner_obj = self.env['res.partner']      
        sale_order_obj = self.env['sale.order']  
        sale_order_line_obj = self.env['sale.order.line']
        product_product_obj = self.env['product.product']
        
        delivery_address = {}
        order_line_info = {}
        inv_address_data = {}
        order_info = {}
        message_info = {}  
        line_no = 1
        order_line = 0
        total_segment = 0
        self.order_type = ''
        
        #read and seprate file in diffrent part
        for segment in csv.reader(file,delimiter="'",quotechar='|'):
            for seg  in segment:
                if seg.startswith('UNB+UNOA') or seg.startswith('UNB+UNOC'):
                    header = seg.split("+")
                    message_info.update({'sender_id' : header[2][:-3],'recipient_id' : header[3][:-3]})
                    total_segment +=1
                    
                elif seg.startswith('UNH'):
                    msg_type = seg.split("+")
                    msg_type = msg_type[2].split(":")[0] if len(msg_type)>2 else ''
                    message_info.update({'message_type' : msg_type})
                    total_segment +=1
                    
                elif seg.startswith('BGM+'):
                    order_name = seg.split("+")
                    order_name = order_name[2] if len(order_name) >= 3 else ''
                    order_info.update({'order_name':order_name})
                    total_segment +=1
                     
                elif seg.startswith('DTM+137'):
                    date_seg = seg.split(":")
                    date_order = datetime.strptime(date_seg[1], '%Y%m%d')
                    order_info.update({'date_order':date_order})
                    total_segment +=1
                        
                elif seg.startswith('DTM+63'):
                    date_seg = seg.split(":")
                    delivery_date = datetime.strptime(date_seg[1], '%Y%m%d')
                    order_info.update({'delivery_date':delivery_date})
                    message_info.update({'max_delivery_date_ept':delivery_date})
                    total_segment +=1
                      
                elif seg.startswith('DTM+64'):
                    date_seg = seg.split(":")
                    earliest_date = datetime.strptime(date_seg[1], '%Y%m%d')
                    message_info.update({'delivery_date_ept' : earliest_date})
                    total_segment +=1
                             
                elif seg.startswith('RFF+ADE'):
                    order = seg.split(":")
                    self.order_type = order[1]
                    total_segment +=1

                elif seg.startswith('RFF+PD'):
                    total_segment +=1
                     
                elif seg.startswith('NAD+BY'):
                    buyer_id = seg.split(":")
                    buyer_address = buyer_id[0][7:]+':'+buyer_id[2]
                    buyer_id = buyer_id and buyer_id[0][7:]
                    message_info.update({'buyer_id':buyer_id,'buyer_address':buyer_address})
                    total_segment +=1
                    continue
                
                elif seg.startswith('NAD+SU'):
                    supplier_id = seg.split(":")
                    supplier_id = supplier_id and supplier_id[0][7:]
                    message_info.update({'supplier_id':supplier_id})
                    total_segment +=1
                    continue
                           
                elif seg.startswith('NAD+DP'):
                    delivery = seg.split("+")
                    delivery_party_id = delivery[2][:-3]
                    country_code = delivery[len(delivery)-1]
                    country_id = country_obj.search([('code', 'ilike', country_code)])
                    message_info.update({'delivery_party_id':delivery_party_id,'country_code':country_code})
                    delivery_address = {'name': delivery[4],
                        'street':delivery[5],
                        'city':delivery[6],
                        'zip':delivery[8],
                        'country_id':country_id.id,
                        }

                    total_segment +=1
                    continue
                #vendors information get from this part
                elif seg.startswith('NAD+IV'):
                    invoice_seg = seg.split("+")
                    invoice_id = invoice_seg and  invoice_seg[2][:-3]
                    message_info.update({'invoice_id':invoice_id})
                    if invoice_seg[4].find(":") >= 0 :
                        customer = invoice_seg[4].split(":")
                    elif invoice_seg[4].find(",") >=0:
                        customer = invoice_seg[4].split(",")
                    country_id = country_obj.search([('code', 'ilike', invoice_seg[9])])

                    #partner_id = partner_obj.search([('name', '=', customer[0])],)
                    partner_id = vendor.so_customer_id
#                     if not partner_id:
#                         partner_vals = {'name':customer[0],'opt_out':True}
#                         partner_id = partner_obj.create(partner_vals)
                    inv_address_data = {
                        'type':'invoice',
                        'name': "%s" %(customer[0]),
                        'street': customer[1],
                        'street2': invoice_seg[5],
                        'city': invoice_seg[6],
                        'zip': invoice_seg[8],
                        'country_id': country_id[0].id if country_id else False,
                        'parent_id': partner_id.id,
                        }
                    if delivery_address:
                        delivery_address.update({'parent_id': partner_id.id,'type':'delivery'})
                        order_info.update({'delivery_address': delivery_address})
                    order_info.update({'inv_address_data':inv_address_data})                    
#                     customer_info.append(inv_address_data)
                    total_segment +=1  
                    continue       
                                         
                elif seg.startswith('RFF+VA'):
                    vat_number = seg.split(":")
                    message_info.update({'vat_number':vat_number[1]})
                    total_segment +=1
                    continue
                
                elif seg.startswith('CUX+2'):
                    currancy = seg.split(":")
                    currancy_code = currancy[1]
                    currency_id = self.env['res.currency'].search([('name','=',currancy_code)])
                    currency_id = currency_id and currency_id[0] or False
                    pricelist_id = vendor and vendor.pricelist_id or False
                    pricelist_id = pricelist_id and pricelist_id.id or False
                    order_info.update({'currency_id':currency_id.id,'pricelist_id':pricelist_id})
                    message_info.update({'currancy_code':currancy_code})
                    total_segment +=1
                    continue
                #sale order line data saprate here
                elif seg.startswith('LIN+'):
                    order_line_info.update({'Line_'+str(line_no):{}})
                    ean = seg.split("+")
                    ean = ean[len(ean)-1] 
                    if ean.upper().find('EN',0,len(ean)) !=-1 and ean.upper().find(':',0,len(ean)) !=-1:
                        ean = ean.split(":") and ean.split(":")[0] or ''
                        order_line_info['Line_'+str(line_no)].update({'ean':ean})
                    #UP used for Universal Product Code **code edited here**
                    elif ean.upper().find('UP',0,len(ean)) !=-1 and ean.upper().find(':',0,len(ean)) !=-1:
                        ean = ean.split(":") and ean.split(":")[0] or ''
                        order_line_info['Line_'+str(line_no)].update({'ean':ean})
                    line_no += 1
                    order_line +=1
                    total_segment +=1
                    
                elif seg.startswith('PIA+'):
                    code = seg.split("+") 
                    code = code[2][:-3] if len(code)>2 else ''
                    if not order_line_info['Line_'+str(line_no-1)].get('ean',False):
                        order_line_info['Line_'+str(line_no-1)].update({'default_code':code})
                    total_segment +=1
                    
                elif seg.startswith('QTY+'):
                    qty = seg.split(":") 
                    qty = qty[1] if len(qty)>1 else 0
                    order_line_info['Line_'+str(line_no-1)].update({'qty':qty})
                    total_segment +=1
                    
                elif seg.startswith('PRI+'):
                    price = seg.split(":") 
                    price = price[1] if len(price)>1 else 0
                    order_line_info['Line_'+str(line_no-1)].update({'price':price})
                    total_segment +=1       
                                          
                elif seg.startswith('UNS+S'):
                    total_segment +=1
                    
                elif seg.startswith('CNT+2'):
                    total_line = seg.split(":") 
                    total_line = total_line[1] if len(total_line)>1 else 0
                    total_segment +=1
                    
                    if int(total_line) != order_line:
                        raise osv.except_osv(_('Error'), _('Order Line not integrated properly, Please Check order line data in file.'))                                                
                    
                elif seg.startswith('UNT+'):
                    segments = seg.split("+")
                    segments = segments[1]
                    if int(segments) != total_segment:
                        raise osv.except_osv(_('Error'), _('File not integrated properly, Please Check file data.'))

        if not vendor.supplier_id == message_info.get('supplier_id', ''):
            if not self.job_id:
                avc_file_process_job_vals = {
                    'message':'Mismatch Supplier Information',
                    'filename':self.server_filename,
                    'vendor_id':vendor.id,
                    'application':'sale_order',
                    'operation_type':'import',
                    'create_date':datetime.now(),
                    'company_id':vendor.company_id.id or False,
                }
                self.job_id = self.create_avc_file_process_job(avc_file_process_job_vals)
            return True
        
        if not vendor.pricelist_id.currency_id.id == order_info.get('currency_id'):
            if not self.job_id:
                avc_file_process_job_vals = {
                    'message':'Mismatch Pricelist information',
                    'filename':self.server_filename,
                    'vendor_id':vendor.id,
                    'application':'sale_order',
                    'operation_type':'import',
                    'create_date':datetime.now(),
                    'company_id':vendor.company_id.id or False,
                }
                self.job_id = self.create_avc_file_process_job(avc_file_process_job_vals)
            return True
        #checked if order exist or not
        existing_order_id = sale_order_obj.search([('amazon_edi_order_id', '=', order_info.get('order_name', ''))])
        if self.order_type == 'firstorder':
            if existing_order_id:
                return True

        #message_id = self.env['amazon.edi.message.info'].create(message_info)
        order_vals = self.prepare_order_vals(vendor,order_info,message_info.get('delivery_party_id',False))
        order_vals.update({'vendor_id':vendor.id,'account_type':self.order_type, 'carrier_id':vendor.amazon_edi_carrier_method.id or False})
        order_vals.update(message_info)
        if vendor.warehouse_id : 
            order_vals.update({'warehouse_id':vendor.warehouse_id.id})
        order_id = sale_order_obj.create(order_vals)
        #message_id.write({'order_id':order_id.id})
        #self.order_id = order_id 
        fiscal_position_id = order_vals.get('fiscal_position_id',False)
        fiscal_position = self.env['account.fiscal.position'].browse(fiscal_position_id) or False        
        line_id = False
        
        #CREATE LOG IN avc.file.transaction.log
        avc_file_process_job_vals = {
                        'message': 'Order imported',
                        'filename': self.server_filename,
                        'vendor_id': vendor.id,
                        'application' : 'sale_order',
                        'operation_type' : 'import',
                        'create_date' : datetime.now(),
                        'company_id':vendor.company_id.id or False,
                        'sale_order_id':order_id.id,
                        }
        self.job_id = self.create_avc_file_process_job(avc_file_process_job_vals)
        
        for key,value in order_line_info.items():
            default_code = value.get('default_code',False)
            ean = value.get('ean',False)
            product = False
            if default_code:
                product = product_product_obj.search([('amazon_sku','=',default_code)])
                if not product :
                    product = product_product_obj.search([('default_code','=',default_code)]) 
                code_type="SKU"
                amazon_code = default_code
                amazon_edi_line_code_type = 'sku'
            if ean :
                product = product_product_obj.search([('barcode','=',ean)])
                code_type = "barcode"
                amazon_code = ean
                amazon_edi_line_code_type = 'barcode'
            orderlinevals ={}
            line = ()
            if product:
                qty = value.get('qty',0.0)
                price = value.get('price',0.0) 
                line=(product,price,amazon_code,qty)
                
                orderlinevals,product_id, qty_code = self.prepare_order_line_vals(line,order_id)
                orderlinevals.update({'amazon_edi_line_code_type' : amazon_edi_line_code_type})
                if orderlinevals:
                    sale_order_line_id = sale_order_line_obj.create(orderlinevals)
                    
                    avc_transaction_log_val = {
                        'message':'Sale Order Line Created',
                        'remark':'sale order id %s'%(order_id.name or ''),
                        'sale_order_id':order_id.id,
                        'job_id':self.job_id.id,
                        'picking_id':False,
                        'back_order_id':False,
                        'sale_order_line_id':sale_order_line_id.id,
                        'product_id':orderlinevals.get('product_id',''),
                        'package_id':False,
                        'stock_inventory_id':False,
                        'company_id':self.job_id.company_id.id or False,
                        'user_id':self.env.user.id,
                        'picking_state':'draft',
                        'application':'sale_order',
                        'export_qty':orderlinevals.get('product_uom_qty',''),
                        'processed_qty':orderlinevals.get('product_uom_qty',''),
                        'manually_processed':False,
                        'is_mismatch_detail':False,
                        'skip_line':False,
                        'skip_order':False,
                        'filename':self.server_filename,
                        'create_date':datetime.now(),
                        'operation_type':'import',
                        'price':price,
                        }
                    self.job_id.transaction_log_ids.create(avc_transaction_log_val)
                else:
                    line = line + (False,qty_code)
                    self.ack_error_lines.append(line)
                    self.create_avc_transaction_lines(order_id,code_type='SKU',code=code,processed_qty=qty,msg='Product not found',price=price)
            else:
                qty_code = 182
                line = line + (False,qty_code)
                self.ack_error_lines.append(line)
                self.create_avc_transaction_lines(order_id,code_type='barcode',code=amazon_code,processed_qty=qty,msg='Product not found',price=price)
        return True

    @api.multi
    def prepare_order_vals(self,vendor,order_info,delivery_party_id):
        """
        Use: To generate sale order's value based on given information.
        :param order_info: Sale Order required information
        :param delivery_party_id: Delivery Party ID
        :return: sale order values (dict{})
        """
        sale_order_obj = self.env['sale.order']
        partner_obj = self.env['res.partner']
        address_data = order_info.get('inv_address_data',{})
        delivery_address = order_info.get('delivery_address',{})
        partner_id=address_data.get('parent_id',False)
        if not partner_id:
            return
        
        inv_add_domain=[]
        for address in address_data:
            inv_add_domain.append((address,'=',address_data.get(address)))

        inv_add_id = partner_obj.search(inv_add_domain)
        inv_add_id = inv_add_id and inv_add_id[0]        
        if not inv_add_id:
            inv_add_id = partner_obj.create(address_data)
        
        delivert_add_domain=[]
        for address in delivery_address:
            delivert_add_domain.append((address,'=',delivery_address.get(address)))
            
        delivery_add_id = partner_obj.search(delivert_add_domain)
        delivery_add_id = delivery_add_id and delivery_add_id[0]
        if not delivery_add_id:
            delivery_add_id = partner_obj.create(delivery_address)
            
        delivery_id = partner_obj.search([('edi_gln_no','=',delivery_party_id),('parent_id','=',partner_id)])
        if not delivery_id:
            delivery_id = partner_obj.search([('edi_gln_no','=',delivery_party_id)])
            if delivery_id and delivery_id.id != partner_id:
                delivery_id.write({'parent_id':partner_id})
            else:
                partner_obj.browse(partner_id).write({'edi_gln_no': delivery_party_id})

        partner_address = partner_obj.browse(partner_id).address_get(['contact','invoice','delivery'])
        
        ordervals={
                   'company_id':vendor.company_id.id or False,
                   'partner_id' :partner_address.get('contact',False),
                   }
        new_record = sale_order_obj.new(ordervals)
        new_record.onchange_partner_id()
        ordervals = sale_order_obj._convert_to_write({name: new_record[name] for name in new_record._cache})
        new_record = sale_order_obj.new(ordervals)
        new_record.onchange_partner_shipping_id()
        ordervals = sale_order_obj._convert_to_write({name: new_record[name] for name in new_record._cache})
        ordervals.update({
                        'name' : order_info.get('order_name'),
                        'amazon_edi_order_id' : order_info.get('order_name',''),
                        'picking_policy' : vendor.picking_policy or False,
                        'date_order' : order_info.get('date_order',False) and order_info['date_order'].strftime('%Y-%m-%d') or time.strftime('%Y-%m-%d'),
                        'state' : 'draft',
                        #'invoice_status' : self.instance_id.amazon_edi_invoice_status or 'invoiced',
                        'mismatch_product' : vendor.mismatch_product,
                        'is_amazon_edi_order' : True,
                        'note': order_info.get('order_name',''),
                        'client_order_ref' : order_info.get('order_name',''),
                        'pricelist_id': order_info.get('pricelist_id',False),
                    })
        return ordervals
    
#     @api.multi
#     def _get_product_stock_for_ack(self,vendor,location_id,company_id):
#         ## Query for get stock based on configuration
# #         location_id = vendor.warehouse_id and vendor.warehouse_id.location_id and vendor.warehouse_id.location_id.id
# #         company_id = vendor.company_id and vendor.company_id.id
#         qry = ""
#         stock_dict = {}
#         if vendor.picking_policy_based_on == 'qty_on_hand' :
#             qry = """
#                     select product_id,sum(quantity)-sum(reserved_quantity)  as total_qty from stock_quant 
#                     where location_id in (%s) and company_id=(%s)
#                     group by product_id
#                   """%(location_id,company_id)
#         if vendor.picking_policy_based_on ==  'forecast_sale' :
#             qry = """
#                     select product_id,sum(total_qty)
#                     from
#                     (
#                     select product_id,sum(quantity)-sum(reserved_quantity)  as total_qty from stock_quant 
#                     where location_id in (%s) and company_id=%s
#                     group by product_id
#                     union all 
#                     select product_id,sum(product_qty) as total_qty from stock_move
#                     where location_dest_id in (%s) and company_id=%s and state not in ('draft','done','cancel')
#                     group by product_id
#                     union all 
#                     select product_id,-sum(product_qty) as total_qty from stock_move
#                     where location_id in (%s) and company_id=%s and state  in ('waiting','confirmed')
#                     group by product_id 
#                     )T
#                     group by product_id
# 
#                   """%(location_id,company_id,location_id,company_id,location_id,company_id)
#         self._cr.execute(qry)
#         results = self._cr.fetchall()
#         for result_tuple in results:
#             stock_dict.update({result_tuple[0] : result_tuple[1]})
#         return stock_dict
    @api.multi
    def prepare_order_line_vals(self,line_info,order_id):
        """
        Use: create sale order line values
        :param line_info: sale order line dict
        :param order_id: sale order id
        :param fiscal_position: fiscal position
        :return: sale_order_line dict{}, product_id, qty_code
        """
        product_id = line_info[0]
        file_price = line_info[1]
        amazon_edi_code = line_info[2]
        qty = float(line_info[3])
        product_product = self.env['product.product']
        sale_order_line_obj = self.env['sale.order.line']
        qty_code = False
        
        #product_id = product_product.search([('default_code','=',default_code)])
        if not product_id:
            qty_code = 182
            return () , product_id, qty_code
        orderlinevals = {
                         'order_id' : order_id.id,
                         'product_id' : product_id.id,
                         }      
        new_record = sale_order_line_obj.new(orderlinevals)
        new_record.product_id_change()
        orderlinevals=new_record._convert_to_write({name: new_record[name] for name in new_record._cache})          
        orderlinevals.update({
            'product_uom_qty' : qty,
            'price_unit' : float(file_price),
            'customer_lead' : product_id and product_id.product_tmpl_id.sale_delay,
            'invoice_status' : 'invoiced',
            'amazon_edi_line_code': amazon_edi_code,
            })
        qty_code = 12
        return orderlinevals, product_id, qty_code

    @api.multi
    def prepare_line(self, fiscal_position=None, product_id=None, order_id=None, qty=None, file_price=None, amazon_edi_code=None):
        """
        Use: Prepare sale order line data with backorder value
        :param fiscal_position: Fiscal Position
        :param product_id: Product ID
        :param order_id: Sale Order ID
        :param qty: Ordered Quantity
        :param file_price: Received price in PO file
        :param amazon_edi_code: Barcode / received from PO file
        :return: sale order line dict{}, product_id, qty_code
        """
        sale_order_line_obj = self.env['sale.order.line']
        tax_id = False
        if fiscal_position:
            tax_id = fiscal_position.map_tax(product_id.taxes_id).ids

        orderlinevals = {
            'order_id':order_id.id,
            'product_id':product_id.id,
        }
        new_record = sale_order_line_obj.new(orderlinevals)
        new_record.product_id_change()
        orderlinevals = new_record._convert_to_write({name:new_record[name] for name in new_record._cache})
        if not orderlinevals.get('tax_id', []):
            tax_id = [(6, 0, tax_id)]
            orderlinevals.update({'tax_id':tax_id})
        orderlinevals.update({
            'product_uom_qty':qty,
            'price_unit':float(file_price),
            'customer_lead':product_id and product_id.product_tmpl_id.sale_delay,
            'invoice_status':'invoiced',
            'amazon_edi_line_code':amazon_edi_code,
        })
        return orderlinevals, product_id

    @api.multi
    def create_avc_file_process_job(self,vals):
        """
        Use: To create new record in avc.file.transaction.log model.
        :param vals: Required Value for avc.file.transaction.log
        :return: avc.file.transaction.log new record ID
        """
        avc_file_process_job_obj=self.env['avc.file.transaction.log']
        job_id = avc_file_process_job_obj.create(vals)
        return job_id
    
    @api.multi
    def create_avc_transaction_lines(self,order,code_type=None,code=None,processed_qty=None,msg=None,price=None,product_id=None):
        """
        Use: To create avc.transaction.log.line new line.
        :param code_type: code information sku/barcode
        :param code: code data
        :param processed_qty: ordered quantity
        :param msg: message for log line
        :param price: price ordered product
        :param product_id: product id if available
        :return: avc.transaction.log.line's id
        """
        #it make an entry in avc.transaction.log.line
        avc_transaction_log_val = {
                    'message':msg if msg else 'Product not Found',
                    'remark': '%s:%s'%(code_type,code),
                    'sale_order_id':order.id,
                    'job_id':self.job_id.id,
                    'company_id':self.job_id.company_id.id or False,
                    'user_id':self.env.user.id,
                    'application':'sale_order',
                    'export_qty':0.0,
                    'processed_qty':processed_qty,
                    'manually_processed':False,
                    'is_mismatch_detail':False if product_id else True,
                    'skip_line':True,
                    'skip_order':False,
                    'filename':self.server_filename,
                    'create_date':datetime.now(),
                    'operation_type':'import',
                    'price':price,
                    'product_id':product_id if product_id else False,
                    }
        res = self.job_id.transaction_log_ids.create(avc_transaction_log_val)
        return res
    
  
 
    
    @api.multi
    def to_pdf417(self,order_id, packages):
        """
        Use: This method called from "report_edi_saleorder_barcode_label" QWeb report.
        This method used for creaate PDF417 format barcode which used in GS1-128 Label.
        :param order_id: sale order id
        :param packages: packages dictionary
        :return: barcode label base64 image data
        """
        sale_order_id = self.browse(order_id)
        text = "AMZN"
        text = text + ',PO: ' + sale_order_id.amazon_edi_order_id
        for package in packages:
            if package.get('barcode'):
                text = text + ',UPC: ' + str(package.get('barcode')) + ','
            else:
                text = text + ',EAN: ' + str(package.get('default_code')) + ','
            text = text + 'QTY: ' + str(package.get('product_qty'))

        print (text)

        codes = encode(text, columns=5)
        image = render_image(codes)
        buffer = StringIO()
        image.save(buffer, format="JPEG")
        img_str = base64.b64encode(buffer.getvalue())

        return img_str
    
    @api.multi
    def get_total_qty(self):
        """
        Use: This method called from "report_edi_saleorder_barcode_label" QWeb report.
        :return: total quantity of selected sale order.
        """
        qty = 0
        for line in self.order_line:
            qty += line.product_uom_qty
        return qty

    @api.multi
    def get_package_information(self,order_id=None):
        """
        Use: To get pericular sale order's Package information.
        :param order_id: sale order id
        :return: dictionary with package information.
        """
        res = {}
        sale_order_id = self.browse(order_id)
        for ids in sale_order_id.picking_ids.pack_operation_product_ids:
            line_info = {'product_id':ids.product_id.id, 'product_qty':ids.product_qty, 'default_code':ids.product_id.default_code or '', 'barcode':ids.product_id.barcode or ''}
            if res.get(ids.result_package_id.name):
                data = res.get(ids.result_package_id.name)
                data.append(line_info)
                res.update({ids.result_package_id.name:data})
            else:
                res.update({ids.result_package_id.name:[line_info]})
        return res

 

    @api.multi
    def _prepare_invoice(self):
        """
        USE: this method call super _prepare_invoice of sale.order after that it checks
            whether current sale order is amazon vendor central's order if yes then it will
            update journal_id which set in amazon vendor instance.
        :return: invoice_value dict
        """
        res = super(sale_order, self)._prepare_invoice()
        if self.is_amazon_edi_order and self.vendor_id.journal_id:
            res.update({'journal_id':self.vendor_id.journal_id.id})
        return res