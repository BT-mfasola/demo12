from odoo import fields, models, api, _
from odoo import models,fields,api,_
from odoo.osv import expression,osv
from datetime import datetime
from ftplib import FTP
from tempfile import NamedTemporaryFile
import time
#import paramiko
import base64
import csv
import time
from io import StringIO,BytesIO

class stock_process_wizard(models.TransientModel):
    _name = 'stock.process.wizard'
    _description = 'stock process wizard'
    
    vendor_id = fields.Many2one('amazon.vendor.instance', string="Vendor Id")
             
    @api.multi
    def prepare_and_send_edi_inventory_message(self):
        """
        use:Generate Inventory information based on selected warehouses in vendor instance.
        :param vendor_id: Amazon Vendor Instance ID
        :param warehouse_for_stock: warehouses selected in Amazon Vendor Instance for stock
        :return: Boolean
        """
        if not self.vendor_id:
            raise osv.except_osv(_('Error'), _('No Vendor Found!!'))

        stock_move_obj = self.env['stock.move']
        #product_product_obj = self.env['product.product'].search([('vendor_id','=',self.vendor_id.id)])
        #amazon_product_ids = self.env['product.product'].search([('is_amazon_product','=',True)]).ids
        #product_ids = product_product_obj.search([('product_tmpl_id','in',amazon_product_ids)])
        product_ids = self.env['product.product'].search([('is_amazon_product','=',True),('vendor_id','=',self.vendor_id.id)])
        currency_name = self.vendor_id.pricelist_id.currency_id.name
        location_ids=[]
        warehouse_gln_number= self.vendor_id.amazon_gln_number
        
        product_lines = []
        for product in product_ids:
            product_qty = product.get_product_stock(product,self.vendor_id)
            pricelist = self.vendor_id.pricelist_id
            price = pricelist and pricelist.with_context(uom=product.uom_id.id).price_get(product.id,1.0,partner=False)[pricelist.id] or 0.0

            product_info={
                'product_id':product.id,
                'product_qty':product_qty if product_qty > 0 else 0,
                'price':price,
                'default_code' : product.default_code,
                'amazon_sku':product.amazon_sku,
                'pricelist_id':currency_name,
                'barcode' : product.barcode
                }
            product_lines.append(product_info)
        if self.vendor_id.file_format_for_export == 'flat_file':
            self.prepare_and_export_inventory_flat_file(self.vendor_id, product_lines, warehouse_gln_number)
        elif self.vendor_id.file_format_for_export == 'edi':
            self.prepare_and_export_inventory_edi(self.vendor_id, product_lines, warehouse_gln_number)
        else:
            raise osv.except_osv(_('Error in Export Inventory'), _(
                "First of all set value in 'File Format' field from 'Amazon Vendor Central >> Configuration >> Vendor "))
        return True

 
    @api.multi
    def prepare_and_export_inventory_edi(self,vendor_id,product_lines, warehouse_gln_number):
        """
        Use: Generate Inventory EDI file.
        :param vendor_id: Amazon Vendor Instance ID(Browseble object).
        :param product_lines: Product dict(product_id, product_qty, sku, barcode).
        :param warehouse_gln_number: Unique number assigned by Amazon to vendor's warehouse.
        :return: Boolean
        """
        #file_order_ship = NamedTemporaryFile(delete=False)
        #currency_name = ''
        currency_name = self.vendor_id.pricelist_id.currency_id.name
        warehouse_gln_number= self.vendor_id.amazon_gln_number
        seq = self.env['ir.sequence'].get('amazon.edi.inventory.number')
        seq_interchange = self.env['ir.sequence'].get('amazon.edi.ship.message.trailer')
        inventory = NamedTemporaryFile(delete=False)
        total_segment = 0
        file_inventory = ""
        
        file_inventory = file_inventory + """UNB+UNOC:2+%s:%s+%s:%s+%s:%s+%s+++++EANCOM'"""%(str(vendor_id.supplier_id),vendor_id.vendor_qualifier,vendor_id.amazon_unb_id or '',vendor_id.amazon_qualifier,time.strftime("%y%m%d"),time.strftime("%H%M"),str(seq_interchange))
        total_segment +=1
        
        
        file_inventory =  file_inventory + """UNH+1+INVRPT:D:96A:UN:EAN008'"""
        total_segment +=1
        
        file_inventory = file_inventory + """BGM+35+%s+9'"""%(str(seq))
        total_segment +=1
        
        file_inventory = file_inventory + """DTM+137:%s:102'"""%(time.strftime("%Y%m%d"))
        total_segment +=1
        
        file_inventory =  file_inventory + """DTM+366:%s:102'"""%(time.strftime("%Y%m%d"))
        total_segment += 1
        
        file_inventory = file_inventory + """NAD+SU+%s::9'"""%(str(vendor_id.supplier_id))
        total_segment +=1
        
        file_inventory = file_inventory + """NAD+WH+%s::9'"""%(warehouse_gln_number)
        total_segment += 1
        
        file_inventory = file_inventory + """CUX+2:%s:10'""" % (currency_name)
        total_segment += 1

        line_no=0
        for line in product_lines:
            product_id = line.get('product_id')
            amazon_sku = line.get('amazon_sku','')
            default_code = line.get('default_code')
            barcode = line.get('barcode','')
            product_qty = line.get('product_qty',0)
            price = line.get('price',0)
            line_no +=1
            
            if barcode == amazon_sku:
                file_inventory = file_inventory + """LIN+%s++%s:EN'"""%(str(line_no),amazon_sku)
                total_segment += 1
            if default_code == amazon_sku:
                file_inventory = file_inventory + """LIN+%s'"""%(str(line_no))
                total_segment +=1
                file_inventory = file_inventory +  """PIA+5+%s:SA'"""%(amazon_sku)
                total_segment +=1
            file_inventory = file_inventory + """QTY+145:%s'"""%(str(product_qty))
            total_segment +=1
            file_inventory = file_inventory + """PRI+AAA:%s'"""%(str(price))
            total_segment +=1
            file_inventory = file_inventory + """CUX+2:%s:10'"""%(currency_name)
            total_segment += 1
#             if line.get('incoming_product_qty',''):
#                 file_inventory = file_inventory + """QTY+21:%s'""" % (str(line.get('incoming_product_qty','')))
#                 total_segment += 1
#                 file_inventory = file_inventory + """DTM+11:%s:102'""" % (line.get('date_expected',''))
#                 total_segment += 1

        file_inventory = file_inventory + """UNT+%s+%s'"""%(str(total_segment),str(seq))
        file_inventory = file_inventory + """UNZ+1+%s'"""%(str(seq_interchange))
        
        #file_inventory.close()
        
        output = StringIO()
        result=base64.b64encode(file_inventory.encode())
        output.write(file_inventory)
        output.seek(0)
        inventory.write(output.read().encode())
        inventory.close()
      
        filename = "%s_%s.%s"%(vendor_id.vendor_code,vendor_id.supplier_id,vendor_id.file_format_for_export)
        
        upload_file_name = '%s_%s_%s_%s_%s_%s_%s_%s.%s' % (
            vendor_id.vendor_code,vendor_id.supplier_id, datetime.now().day, datetime.now().month, datetime.now().year, datetime.now().hour,
            datetime.now().minute, datetime.now().second,vendor_id.file_format_for_export)
        
        avc_file_process_job_vals = {
            'message':'Inventory Report Exported ',
            'vendor_id':self.vendor_id.id,
            'filename':upload_file_name,
            'application':'stock_adjust',
            'operation_type':'export',
            'create_date':datetime.now(),
        }
        job_id = self.env['avc.file.transaction.log'].create(avc_file_process_job_vals)
       # job_id.write({'transaction_log_ids' : [(6,0,transaction_lines)]})
        vals = {
            'name':upload_file_name,
            'datas':result,
            'datas_fname':upload_file_name,
            'res_model':'avc.file.transaction.log',
            'type':'binary',
            'res_id':self.vendor_id.id,
        }
        #self.vendor_id.write({'filename':upload_file_name})
        attachment = self.env['ir.attachment'].create(vals)
        job_id.write({'attachment_id' : attachment.id})  
        job_id.message_post(body=_("<b>Stock Inventory and Cost Report </b>"),attachment_ids=attachment.ids)
        
        """
        This File Generate in Ftp upload Folder. Remove below Code.
        """

        connection_id = False
        if vendor_id.is_production_environment:
            ftp_server_id = vendor_id.production_ftp_connection
            directory_id = vendor_id.production_inv_cost_directory_id
        else :
            ftp_server_id = vendor_id.test_ftp_connection
            directory_id = vendor_id.test_inv_cost_directory_id
        with vendor_id.get_edi_sending_interface(ftp_server_id,directory_id) \
                as edi_interface:
            edi_interface.push_to_ftp(filename,inventory.name)
        return True

    @api.multi
    def prepare_and_export_inventory_flat_file(self,vendor_id,product_lines, warehouse_gln_number):
        """
        USE: here inventory and cost flat file prepare and send to amazon.
        static header used : ISBN|EAN|UPC|VENDOR_STOCK_ID|TITLE|QTY_ON_HAND|LIST_PRICE_EXCL_TAX|LIST_PRICE_INCL_TAX|COST_PRICE|DISCOUNT|ISO_CURRENCY_CODE
        :param vendor_id:
        :param product_lines:
        :param warehouse_gln_number:
        :return:
        """
        """
        This File Generate in Ftp upload Folder. Remove below Code.
        """
        inventory = NamedTemporaryFile(delete=False)
        file_inventory = ""
        file_inventory = file_inventory +  """ISBN|EAN|UPC|VENDOR_STOCK_ID|TITLE|QTY_ON_HAND|LIST_PRICE_EXCL_TAX|LIST_PRICE_INCL_TAX|COST_PRICE|DISCOUNT|ISO_CURRENCY_CODE\n"""
        for product in product_lines:
            file_inventory = file_inventory + """|%s||%s|%s|%s|||%s||%s||%s\n""" % (str(product.get('barcode','')),product.get('amazon_sku',''),product.get('product_name',''),str(int(product.get('product_qty',0))),str(product.get('price',0)),self.env.user.currency_id.name,vendor_id.production_feed_key)

        #file_inventory.close()

        output = StringIO()
        result=base64.b64encode(file_inventory.encode())
        output.write(file_inventory)
        output.seek(0)
        inventory.write(output.read().encode())
        inventory.close()
      
        filename = "%s_%s.%s"%(vendor_id.vendor_code,vendor_id.supplier_id,vendor_id.file_format_for_export)
        
        upload_file_name = '%s_%s_%s_%s_%s_%s_%s_%s.%s' % (
            vendor_id.vendor_code,vendor_id.supplier_id, datetime.now().day, datetime.now().month, datetime.now().year, datetime.now().hour,
            datetime.now().minute, datetime.now().second,vendor_id.file_format_for_export)
        
        avc_file_process_job_vals = {
            'message':'Inventory Report Exported ',
            'vendor_id':self.vendor_id.id,
            'filename':upload_file_name,
            'application':'stock_adjust',
            'operation_type':'export',
            'create_date':datetime.now(),
        }
        job_id = self.env['avc.file.transaction.log'].create(avc_file_process_job_vals)
       # job_id.write({'transaction_log_ids' : [(6,0,transaction_lines)]})
        vals = {
            'name':upload_file_name,
            'datas':result,
            'datas_fname':upload_file_name,
            'res_model':'avc.file.transaction.log',
            'type':'binary',
            'res_id':self.vendor_id.id,
        }
        #self.vendor_id.write({'filename':upload_file_name})
        attachment = self.env['ir.attachment'].create(vals)
        job_id.write({'attachment_id' : attachment.id})  
        job_id.message_post(body=_("<b>Stock Inventory and Cost Report </b>"),attachment_ids=attachment.ids)
        connection_id = False
        if vendor_id.is_production_environment:
            ftp_server_id = vendor_id.production_ftp_connection
            directory_id = vendor_id.production_inv_cost_directory_id
        else :
            ftp_server_id = vendor_id.test_ftp_connection
            directory_id = vendor_id.test_inv_cost_directory_id
        with vendor_id.get_edi_sending_interface(ftp_server_id,directory_id) \
                as edi_interface:
            edi_interface.push_to_ftp(filename,inventory.name)
        return True
                
    @api.multi
    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}
  
