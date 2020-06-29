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

class Product_Product(models.Model):
    _inherit = 'product.product'

    suggested_price = fields.Float(string = 'Suggested Price')
    amazon_sku = fields.Char(string="Amazon sku")
    vendor_id = fields.Many2one('amazon.vendor.instance',string='Vendor')
    is_amazon_product = fields.Boolean(string = 'Is Amazon Product')
    
    @api.multi
    def get_product_stock(self,product,vendor):
        if vendor.product_stock_field_id :
            stock_field = vendor.product_stock_field_id.name
        else :
            stock_field = 'virtual_available'
        warehouse_ids = vendor.warehouse_ids
        qty_to_update = 0.0
        actual_stock = 0.0
        if warehouse_ids:
            product = self.env['product.product'].with_context(warehouse=warehouse_ids.ids).browse(product.id)
            if hasattr(product, stock_field):
                actual_stock = getattr(product,stock_field)
            else:
                actual_stock = product.qty_available
        return actual_stock 
    
#       
# class ProductTemplate(models.Model):
#     _inherit = 'product.template'
#     
#     #is_amazon_product = fields.Boolean(string = 'Is Amazon Product')
#     
#     @api.multi
#     def prepare_and_send_edi_inventory_message(self,vendor_id=None, warehouse_for_stock=None):
#         """
#         use:Generate Inventory information based on selected warehouses in vendor instance.
#         :param vendor_id: Amazon Vendor Instance ID
#         :param warehouse_for_stock: warehouses selected in Amazon Vendor Instance for stock
#         :return: Boolean
#         """
#         if not vendor_id:
#             raise osv.except_osv(_('Error'), _('No Vendor Found!!'))
#         if not warehouse_for_stock:
#             raise osv.except_osv(_('Error'), _('No Warehouse found for Stock..!!\n Select Warehouser for Stock first.'))
# 
#         stock_move_obj = self.env['stock.move']
#         product_product_obj = self.env['product.product']
#         amazon_product_ids = self.search([('is_amazon_product','=',True)]).ids
#         product_ids = product_product_obj.search([('product_tmpl_id','in',amazon_product_ids)])
#         location_ids=[]
#         warehouse_gln_number=''
#         for warehouse in warehouse_for_stock:
#             location_ids.append(warehouse.lot_stock_id.id)
#             warehouse_gln_number = warehouse.gln_number
#         product_lines=[]
#         incoming_product_lines = []
#         for product in product_ids:
#             product_qty = product.with_context(location=location_ids).qty_available
#             product_price = 0.0
#             if vendor_id.sale_price_based_on == 'pricelist':
#                 if not vendor_id.pricelist_id:
#                     raise osv.except_osv(_('Error in Export Inventory'), _(
#                         "First of all set value in 'PriceList' field from 'Amazon Vendor Central >> Configuration >> Vendor "))
#                 product_price = product.with_context(pricelist=vendor_id.pricelist_id.id).price
#             elif vendor_id.sale_price_based_on == 'field':
#                 if not vendor_id.field_id:
#                     raise osv.except_osv(_('Error in Export Inventory'), _(
#                         "First of all set value in 'Field' field from 'Amazon Vendor Central >> Configuration >> Vendor "))
#                 product_price = getattr(product,vendor_id.field_id.name)
#             else:
#                 raise osv.except_osv(_('Error in Export Inventory'),_("First of all set value in 'Sale Price besed on' field from 'Amazon Vendor Central >> Configuration >> Vendor "))
#             product_info={
#                 'product_id':product.id,
#                 'product_qty':product_qty if product_qty > 0 else 0,
#                 'price':product_price,
#                 'sku':product.default_code or '',
#                 'barcode':product.barcode or '',
#                 'product_name':product.name,
#                 }
#             if vendor_id.include_forecast_incoming:
#                 stock_move_ids = stock_move_obj.search([('product_id','=',product.id),('location_dest_id','in',location_ids),('state','=','assigned')])
#                 product_uom_qty = 0.0
#                 if stock_move_ids:
#                     for stock_move in stock_move_ids:
#                         date_expected = stock_move.date_expected
#                         product_uom_qty += stock_move.product_uom_qty
#                     product_info.update({'date_expected':datetime.strptime(date_expected, '%Y-%m-%d %H:%M:%S').strftime("%Y%m%d"), 'incoming_product_qty':product_uom_qty})
#             product_lines.append(product_info)
#         if vendor_id.file_format_for_export == 'flat_file':
#             self.prepare_and_export_inventory_flat_file(vendor_id, product_lines, warehouse_gln_number)
#         elif vendor_id.file_format_for_export == 'edi':
#             self.prepare_and_export_inventory_edi(vendor_id, product_lines, warehouse_gln_number)
#         else:
#             raise osv.except_osv(_('Error in Export Inventory'), _(
#                 "First of all set value in 'File Format' field from 'Amazon Vendor Central >> Configuration >> Vendor "))
#         return True
#         
#     @api.multi
#     def prepare_and_export_inventory_edi(self,vendor_id,product_lines, warehouse_gln_number):
#         """
#         Use: Generate Inventory EDI file.
#         :param vendor_id: Amazon Vendor Instance ID(Browseble object).
#         :param product_lines: Product dict(product_id, product_qty, sku, barcode).
#         :param warehouse_gln_number: Unique number assigned by Amazon to vendor's warehouse.
#         :return: Boolean
#         """
#         currency_name = ''
#         if vendor_id.sale_price_based_on == 'pricelist':
#             currency_name = vendor_id.pricelist_id.currency_id.name
#         elif vendor_id.sale_price_based_on == 'field':
#             currency_name = self.env.user.currency_id.name
#         seq = self.env['ir.sequence'].get('amazon.edi.inventory.number')
#         seq_interchange = self.env['ir.sequence'].get('amazon.edi.ship.message.trailer')
#         file_inventory = NamedTemporaryFile(delete=False)
#         total_segment = 0
#         
#         file_inventory.write("""UNB+UNOC:2+%s:%s+%s:%s+%s:%s+%s+++++EANCOM'"""%(str(vendor_id.supplier_id),vendor_id.vendor_qualifier,vendor_id.amazon_unb_id or '',vendor_id.amazon_qualifier,time.strftime("%y%m%d"),time.strftime("%H%M"),str(seq_interchange)))
#         total_segment +=1
#         file_inventory.write("""UNH+1+INVRPT:D:96A:UN:EAN008'""")
#         total_segment +=1
#         file_inventory.write("""BGM+35+%s+9'"""%(str(seq)))
#         total_segment +=1
#         file_inventory.write("""DTM+137:%s:102'"""%(time.strftime("%Y%m%d")))
#         total_segment +=1
#         file_inventory.write("""DTM+366:%s:102'"""%(time.strftime("%Y%m%d")))
#         total_segment += 1
#         file_inventory.write("""NAD+SU+%s::9'"""%(str(vendor_id.supplier_id)))
#         total_segment +=1
#         file_inventory.write("""NAD+WH+%s::9'"""%(warehouse_gln_number))
#         total_segment += 1
#         file_inventory.write("""CUX+2:%s:10'""" % (currency_name))
#         total_segment += 1
# 
#         line_no=0
#         for line in product_lines:
#             product_id = line.get('product_id')
#             sku = line.get('sku','')
#             barcode = line.get('barcode','')
#             product_qty = line.get('product_qty',0)
#             price = line.get('price',0)
#             line_no +=1
#             if barcode:
#                 file_inventory.write("""LIN+%s++%s:EN'"""%(str(line_no),barcode))
#                 total_segment += 1
#             else:
#                 file_inventory.write("""LIN+%s'"""%(str(line_no)))
#                 total_segment +=1
#                 file_inventory.write("""PIA+5+%s:SA'"""%(sku))
#                 total_segment +=1
#             file_inventory.write("""QTY+145:%s'"""%(str(product_qty)))
#             total_segment +=1
#             file_inventory.write("""PRI+AAA:%s'"""%(str(price)))
#             total_segment +=1
#             file_inventory.write("""CUX+2:%s:10'"""%(currency_name))
#             total_segment += 1
#             if line.get('incoming_product_qty',''):
#                 file_inventory.write("""QTY+21:%s'""" % (str(line.get('incoming_product_qty',''))))
#                 total_segment += 1
#                 file_inventory.write("""DTM+11:%s:102'""" % (line.get('date_expected','')))
#                 total_segment += 1
# 
#         file_inventory.write("""UNT+%s+%s'"""%(str(total_segment),str(seq)))
#         file_inventory.write("""UNZ+1+%s'"""%(str(seq_interchange)))
#         
#         file_inventory.close()
# 
#         fl = file(file_inventory.name, 'rb')
#         out = base64.encodestring(fl.read())
# 
#         avc_file_transaction_job_value={
#             'message': 'Inventory exported',
#             'vendor_id': vendor_id.id,
#             'application' : 'stock_adjust',
#             'operation_type' : 'export',
#             'create_date' : datetime.now(),
#             'company_id':vendor_id.company_id.id or False,
#             }
#         job_id = self.env['avc.file.transaction.log'].create(avc_file_transaction_job_value)
#         filename = "INVRPT_.txt"
#         upload_file_name = '%s_%s_%s_%s_%s_%s_%s.mgc'%(filename,datetime.now().day,datetime.now().month,datetime.now().year,datetime.now().hour,datetime.now().minute,datetime.now().second)
#         vals = {
#             'name':upload_file_name,
#             'datas':out,
#             'datas_fname':upload_file_name,
#             'res_model':'avc.file.transaction.log',
#             'type':'binary',
#             'res_id':job_id,
#             }
#         
#         attachment = self.env['ir.attachment'].create(vals)     
#         job_id.message_post(body=_("<b>Inventory exported file</b>"),attachment_ids=attachment.ids)
#         fl.close()
#         connection_id = False
#         if vendor_id.inventory_connection_type == 'test_connection':
#             connection_id = vendor_id.inventory_test_ftp_id
#         elif vendor_id.inventory_connection_type == 'production_connection':
#             connection_id = vendor_id.inventory_production_ftp_id
#         else:
#             raise osv.except_osv(_('Error'),_('First of all select Connection detail.! \nAmazon Vendor Central >> Configuration >> Vendor >> Inventory'))
#         with vendor_id.get_new_edi_sending_interface(connection_id) \
#                     as edi_interface:
#             edi_interface.push_to_ftp(filename, file_inventory.name)
#         job_id.write({'filename':upload_file_name})
#         return True 
# 
#     @api.multi
#     def prepare_and_export_inventory_flat_file(self,vendor_id,product_lines, warehouse_gln_number):
#         """
#         USE: here inventory and cost flat file prepare and send to amazon.
#         static header used : ISBN|EAN|UPC|VENDOR_STOCK_ID|TITLE|QTY_ON_HAND|LIST_PRICE_EXCL_TAX|LIST_PRICE_INCL_TAX|COST_PRICE|DISCOUNT|ISO_CURRENCY_CODE
#         :param vendor_id:
#         :param product_lines:
#         :param warehouse_gln_number:
#         :return:
#         """
#         connection_id = False
#         feed_key = '<feed_key>'
#         if vendor_id.inventory_connection_type == 'test_connection':
#             connection_id = vendor_id.inventory_test_ftp_id
#         elif vendor_id.inventory_connection_type == 'production_connection':
#             connection_id = vendor_id.inventory_production_ftp_id
#             feed_key = vendor_id.production_feed_key
#         else:
#             raise osv.except_osv(_('Error'), _(
#                     'First of all select Connection detail.! \nAmazon Vendor Central >> Configuration >> Vendor >> Inventory'))
#         file_inventory = NamedTemporaryFile(delete=False)
#         file_inventory.write("""ISBN|EAN|UPC|VENDOR_STOCK_ID|TITLE|QTY_ON_HAND|LIST_PRICE_EXCL_TAX|LIST_PRICE_INCL_TAX|COST_PRICE|DISCOUNT|ISO_CURRENCY_CODE\n""")
#         for product in product_lines:
#             file_inventory.write("""|%s||%s|%s|%s|||%s||%s\n""" % (str(product.get('barcode','')),product.get('sku',''),product.get('product_name',''),str(int(product.get('product_qty',0))),str(product.get('price',0)),self.env.user.currency_id.name))
# 
#         file_inventory.close()
# 
#         fl = file(file_inventory.name, 'rb')
#         out = base64.encodestring(fl.read())
# 
#         avc_file_transaction_job_value = {
#             'message':'Inventory exported Flat File',
#             'vendor_id':vendor_id.id,
#             'application':'stock_adjust',
#             'operation_type':'export',
#             'create_date':datetime.now(),
#             'company_id':vendor_id.company_id.id or False,
#         }
#         job_id = self.env['avc.file.transaction.log'].create(avc_file_transaction_job_value)
#         filename = "RETAIL_FEED_%s_%s_00.TXT" % (feed_key, time.strftime("%Y%m%d"))
#         upload_file_name = '%s_%s_%s_%s_%s_%s_%s.TXT' % (
#         filename, datetime.now().day, datetime.now().month, datetime.now().year, datetime.now().hour,
#         datetime.now().minute, datetime.now().second)
#         vals = {
#             'name':upload_file_name,
#             'datas':out,
#             'datas_fname':upload_file_name,
#             'res_model':'avc.file.transaction.log',
#             'type':'binary',
#             'res_id':job_id,
#         }
# 
#         attachment = self.env['ir.attachment'].create(vals)
#         job_id.message_post(body=_("<b>Inventory exported file</b>"), attachment_ids=attachment.ids)
#         fl.close()
# 
#         with vendor_id.get_new_edi_sending_interface(connection_id) \
#                 as edi_interface:
#             edi_interface.push_to_ftp(filename, file_inventory.name)
#         job_id.write({'filename':upload_file_name})
#         return True
