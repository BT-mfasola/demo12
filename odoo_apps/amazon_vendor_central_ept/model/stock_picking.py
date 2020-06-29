from odoo import models,fields,api,_
from odoo.osv import expression,osv
from odoo.exceptions import Warning
from datetime import datetime
from tempfile import NamedTemporaryFile
import base64
import logging
import time
import csv
from io import StringIO,BytesIO
from dateutil.relativedelta import relativedelta
_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def batch_picking_package_report(self):
        return self.env.ref('amazon_vendor_central_ept.report_package_labels').report_action(self)
    
    @api.depends('package_ids')
    def _calculate_gross_weight(self):
        for record in self:
            if record.is_amazon_edi_picking :
                gross_weight = 0.0
                for package in record.package_ids :
                    gross_weight = gross_weight + package.amazon_package_weight
                record.gross_weight = gross_weight
            
    @api.depends('package_ids')
    def _calculate_gross_volume(self):
        for record in self:
            if record.is_amazon_edi_picking:
                gross_volume = 0.0
                for package in record.package_ids:
                    box = package.packaging_id
                    box_volume = box.height * box.length * box.width
                    gross_volume = gross_volume + box_volume
                record.gross_volume = gross_volume
            
    is_amazon_edi_picking = fields.Boolean(string = 'Is Amazon Picking', compute = '_get_avc_info')
    vendor_id = fields.Many2one('amazon.vendor.instance',string="Amazon Vendor")
    po_ack_uploaded = fields.Boolean(string = 'Purchase Order Acknowledgement Sent')
    carrier_type = fields.Selection([('wepay','WePay'),('we_not_pay', 'We not Pay')])
    carrier_id = fields.Many2one('delivery.carrier', string = 'Delivery Carrier', compute = '_get_avc_info')
    delivery_date = fields.Datetime(string = 'Delivery Date')
    dispatch_date = fields.Datetime(string = 'Dispatch Date')
    sale_order_id = fields.Many2one('sale.order', string = 'Sale Order')
    bol_number = fields.Char(string = 'Bill of Lading Number')
    gross_weight = fields.Float(string = 'Gross Weight',compute="_calculate_gross_weight")
    gross_volume = fields.Float(string = 'Gross Volume',compute="_calculate_gross_volume")
    goods_description = fields.Selection([('Hazardous_materials','Hazardous materials'),
                                          ('Refrigerated_food','Refrigerated food'),
                                          ('Frozen_food','Frozen food'),
                                          ('Temperature_controlled_food','Temperature controlled food'),
                                          ('Food','Food'),('Magnetic','Magnetic'),
                                          ('Separate_from_Magnetic_Goods','Separate from Magnetic Goods'),
                                          ('Heavy/Bulky','Heavy/Bulky'),
                                          ('High_value_goods','High value goods'),('Standard','Standard'),], default = 'Hazardous_materials')
    
    booking_ref_number = fields.Char(string='Booking Reference Number')
    additional_ref_number = fields.Char(string = 'Additional Reference Number')
    loading_type = fields.Selection([('PACKAGE','Package'),('TL','Truck Load'),('LTL','Less then a Truck Load'),])
    loading_value = fields.Selection([('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High'), ])
    pickup_date = fields.Datetime(string = 'Pick-up Date Time')
    carrier_scac_id = fields.Char(string = 'Carrier SCAC ID')
    carrier_name = fields.Char(string = 'Carrier Name')
    sscc_code = fields.Char(string = 'Serial Shipping Container Code')
    is_package_info_imported = fields.Boolean('Is Package Info Imported?')
    route_request_send = fields.Boolean("Routing Request send")
    routing_instruction_received = fields.Boolean(string = 'Routing Instruction Received')
    shipment_notice_send = fields.Boolean(string="Shipment Notice Send")
    #NOTE: here intentionally KEY set as numeric, because this tag are working together for display Value.
    mode_of_transport = fields.Selection([('10+13','Carriage by Sea'),
                                          ('20+25','Carriage by Rail'),
                                          ('30+31','Road Haulage'),
                                          ('40+41','Carriage by Air')], string = 'Mode of Transport')

    @api.multi
    @api.depends('sale_id')
    def _get_avc_info(self):
        for line in self:
            line.is_amazon_edi_picking = line.sale_id.is_amazon_edi_order
            line.sale_order_id = line.sale_id.id
            line.carrier_id = line.sale_id.carrier_id.id

    @api.multi
    def export_po_ack(self):
        """
        USE: export_po_ack method called from stock.picking's 'Export POA' button,
        based on stock.picking and Amazon PO's information it will create POA EDI file
        and send it to Amazon Vendor Central.
        :return: Boolean
        """
        avc_file_transaction_job_obj = self.env['avc.file.transaction.log']
        avc_transaction_log_obj = self.env['avc.transaction.log.line']
        vendor_id = self.sale_id.vendor_id

        mismatch_product = self.sale_id.mismatch_product
        self.action_assign()
        order_line_info = []
        error_line_info = []
        if self.move_lines:
            avc_file_process_job_vals = {
                    'message':'PO Acknowledgement Export',
                    'vendor_id':vendor_id.id,
                    'application':'sale_order_response',
                    'operation_type':'export',
                    'create_date':datetime.now(),
                    'company_id':self.env.user.company_id.id,
                    'sale_order_id':self.sale_id.id,
                }
            self.job_id = avc_file_transaction_job_obj.create(avc_file_process_job_vals)
        order_info = {
                'order_name' : self.sale_id.amazon_edi_order_id,
                'schedule_date' : self.scheduled_date,
                
            }
        for line in self.move_lines:
            reserved_qty = line.reserved_availability
            order_qty = line.product_uom_qty
            amazon_line_code = line.sale_line_id.amazon_edi_line_code
            price_unit = line.sale_line_id.price_unit
            total_price = line.sale_line_id.price_subtotal
            reserved_qty_price = reserved_qty * price_unit
            backorder_qty = order_qty - reserved_qty
            cancel_qty = order_qty - reserved_qty
            line_info = {
                        'product_id' : line.product_id,
                        'reserved_qty' : reserved_qty,
                        'order_qty' : order_qty,
                        'unit_price' : price_unit,
                        'total_price' : total_price,
                        'reserved_qty_price' : reserved_qty_price,
                        'amazon_line_code' : amazon_line_code,
                        'sale_line_id' : line.sale_line_id,
                        'is_mismatch' : False,
                        'amazon_edi_line_code_type' : line.sale_line_id.amazon_edi_line_code_type
                    }
            if mismatch_product == 'backorder' : 
                line_info.update({'backorder_qty' : backorder_qty})
            if mismatch_product == 'cancel' :
                line_info.update({'cancel_qty' : cancel_qty})
            order_line_info.append(line_info)
            
        mismatch_lines =  avc_transaction_log_obj.search([('sale_order_id', '=', self.sale_id.id), ('operation_type', '=', 'import'),('is_mismatch_detail', '=', True)])
        for mismatch_line in mismatch_lines:
            remark = mismatch_line.remark.split(':')
            error_line = {
                    'remark' : mismatch_line.remark,
                    'amazon_line_code' : remark[1],
                    'is_mismatch' : True,
                    'unit_price' : mismatch_line.price,
                    'amazon_edi_line_code_type' : remark[0],
                    'qty' : mismatch_line.processed_qty,
                }
            error_line_info.append(error_line)
        message_info = {
            'sender_id':self.sale_id.sender_id,
            'recipient_id':self.sale_id.recipient_id,
            'supplier_id':self.sale_id.supplier_id,
            'delivery_party_id':self.sale_id.delivery_party_id,
            'country_code':self.sale_id.country_code,
            'buyer_address':self.sale_id.buyer_address,
            'buyer_id':self.sale_id.buyer_id,
            'invoice_id':self.sale_id.invoice_id,
            'max_delivery_date':self.sale_id.max_delivery_date_ept or False,
            'delivery_date':self.sale_id.delivery_date_ept or False,
        }
            
        self.prepare_order_ship_notice(vendor_id, order_info, message_info, order_line_info,error_line_info)
        return True

    @api.multi
    def prepare_order_ship_notice(self, vendor_id, order_info, message_info, order_line_info,error_line_info):
        """
        USE: Generate EDI file based on provided information of
        Amazon PO, Sale Order, stock.picking's move_lines.
        :param instance_id: vendor_id or instance_id
        :param order_info: Sale Order information dictionary
        :param message_info: other required PO's information
        :param order_line_info: sale order line information
        :return: Boolean
        """
        file_order_ship = NamedTemporaryFile(delete=False)
        total_segment = 0
        po_ack_file_string = ""
        self.export_avc_line_id = []
        if not message_info.get('sender_id', False) or not message_info.get('recipient_id', False):
            raise osv.except_osv(_('Error'), _('Sender or recipient identifier not found.'))
        product_product_obj = self.env['product.product']
        sender_id = message_info.get('sender_id',False)
        recipient_id = message_info.get('recipient_id',False)
        seq_interchange = self.env['ir.sequence'].get('amazon.edi.purchase.order.response')
        po_ack_file_string = po_ack_file_string + "UNB+UNOC:2+%s:%s+%s:%s+%s:%s+%s+++++EANCOM'"%(recipient_id,vendor_id.vendor_qualifier,sender_id,vendor_id.amazon_qualifier,time.strftime("%y%m%d"),time.strftime("%H%M"),str(seq_interchange))
        total_segment += 1
        
        po_ack_file_string = po_ack_file_string + "UNH+1+ORDRSP:D:96A:UN:EAN005'"
        total_segment += 1
        
        po_ack_file_string = po_ack_file_string + "BGM+231+DES%s+29'"%(order_info.get('order_name',''))
        total_segment += 1
        
        po_ack_file_string = po_ack_file_string + "DTM+137:%s:102'"%(time.strftime("%Y%m%d"))
        total_segment += 1
        
        po_ack_file_string = po_ack_file_string + "RFF+ON:%s'" % (order_info.get('order_name', ''))
        total_segment += 1
        
        date_done = order_info.get('schedule_date', time.strftime("%Y%m%d"))
        #date_done = datetime.strptime(date_done, '%Y-%m-%d %H:%M:%S')
        date_done = date_done.strftime("%Y%m%d")
        po_ack_file_string = po_ack_file_string + "DTM+171:%s:102'"%(date_done)
        total_segment += 1
        
        po_ack_file_string = po_ack_file_string + "NAD+SU+%s::9'" %(message_info.get('supplier_id',''))
        total_segment += 1
        
        po_ack_file_string = po_ack_file_string + "NAD+DP+%s::9+++++++%s'"%(message_info.get('delivery_party_id',''),message_info.get('country_code'))
        total_segment += 1
        
        po_ack_file_string = po_ack_file_string + "CUX+2:%s:9'"%(self.sale_id.currency_id.name)
        total_segment += 1

        line_no = 0
        for order_line in order_line_info:
            line_no += 1
            product_id = order_line.get('product_id')
            reserved_qty = order_line.get('reserved_qty',0.0)
            order_qty = order_line.get('order_qty',0.0)
            unit_price = order_line.get('unit_price')
            total_price = order_line.get('total_price')
            reserved_qty_price = order_line.get('reserved_qty_price')
            amazon_line_code = order_line.get('reserved_qty_price')
            sale_line_id = order_line.get('sale_line_id',False) 
            is_mismatch = order_line.get('is_mismatch')
            backorder_qty = order_line.get('backorder_qty',0.0)
            cancel_qty = order_line.get('cancel_qty',0.0)
            amazon_edi_line_code_type = order_line.get('amazon_edi_line_code_type')
            tax_amount = sale_line_id.tax_id and sale_line_id.tax_id[0] and sale_line_id.tax_id.amount or 0.0
            
            avc_transaction_log_val = {}

            if amazon_edi_line_code_type == 'barcode':
                po_ack_file_string = po_ack_file_string + "LIN+%s+5+%s:EN'"%(str(line_no),amazon_line_code)
                total_segment += 1
            if amazon_edi_line_code_type == 'sku':
                po_ack_file_string = po_ack_file_string + "LIN+%s'"%(str(line_no))
                total_segment += 1
                po_ack_file_string = po_ack_file_string + "PIA+5+%s:SA'"%(amazon_line_code)
                total_segment += 1

            if reserved_qty > 0.0 and backorder_qty == 0.0:
                po_ack_file_string = po_ack_file_string + "QTY+12:%s'"%(reserved_qty)
                total_segment += 1
                avc_transaction_log_val.update({'export_qty':reserved_qty})

            if backorder_qty > 0.0:
                backorder_date = self.sale_id.max_delivery_date_ept
                
                #date_done = order_info.get('schedule_date', time.strftime("%Y%m%d"))
                backorder_date = datetime.strptime(backorder_date, '%Y-%m-%d')
                backorder_date = backorder_date.strftime("%Y%m%d")
                
                po_ack_file_string = po_ack_file_string + "QTY+12:%s'"%(str(reserved_qty))
                total_segment +=1
                po_ack_file_string = po_ack_file_string + "QTY+83:%s'"%(str(backorder_qty))
                total_segment += 1
                po_ack_file_string = po_ack_file_string + "DTM+11:%s:102'" % (backorder_date)
                total_segment += 1
                avc_transaction_log_val.update({'export_qty':reserved_qty})

            if cancel_qty and cancel_qty > 0.0:
                po_ack_file_string = po_ack_file_string + "QTY+185:%s'"%(str(cancel_qty))
                total_segment += 1
                avc_transaction_log_val.update({'skip_line':True,'export_qty':reserved_qty})
            
            po_ack_file_string = po_ack_file_string + "PRI+AAA:%s:CT:NTP'"%(unit_price)
            total_segment += 1
            
            if tax_amount > 0.0:
                po_ack_file_string = po_ack_file_string + "TAX+7+VAT+++:::%s'"%(str(tax_amount))
                total_segment += 1

            avc_transaction_log_val.update({
                'message':'Sale Order Line',
                'remark':'sale order name %s' % (self.sale_id.name or ''),
                'sale_order_id':self.sale_id.id,
                'job_id':self.job_id.id,
                'sale_order_line_id':sale_line_id.id,
                'product_id':product_id.id,
                'company_id':self.env.user.company_id.id,
                'user_id':self.env.user.id,
                'picking_state':'draft',
                'application':'sale_order_response',
                'processed_qty':str(order_qty),
                'create_date':datetime.now(),
                'operation_type':'export',
                'price':unit_price,
            })
            res = self.job_id.transaction_log_ids.create(avc_transaction_log_val)
            self.export_avc_line_id.append(res)

        for line in error_line_info:
            line_no += 1
            amazon_line_code = line.get('amazon_line_code')
            is_mismatch = line.get('is_mismatch')
            unit_price = line.get('unit_price')
            remark = line.get('remark')
            amazon_edi_line_code_type = line.get('amazon_edi_line_code_type')
            qty = line.get('qty')
            if amazon_edi_line_code_type == 'barcode':
                po_ack_file_string = po_ack_file_string + "LIN+%s+10+%s:EN'" %(str(line_no),str(amazon_line_code))
                total_segment += 1
            if amazon_edi_line_code_type == 'SKU' :
                po_ack_file_string = po_ack_file_string + "LIN+%s+10'"%(str(line_no))
                total_segment += 1
                po_ack_file_string = po_ack_file_string + "PIA+5+%s:SA'"%(amazon_line_code)
                total_segment += 1
            po_ack_file_string = po_ack_file_string + "QTY+182:%s'"%(qty)
            total_segment += 1
            po_ack_file_string = po_ack_file_string + "PRI+AAA:%s:CT:NTP'"%(str(unit_price))
            total_segment += 1
            po_ack_file_string = po_ack_file_string + "TAX+7+VAT+++:::0'"
            total_segment += 1

            avc_transaction_log_val = {
                'message':'Product not Found',
                'remark':' %s' % (remark),
                'sale_order_id':self.sale_id.id,
                'job_id':self.job_id.id,
                'product_id':product_id.id or False,
                'company_id':self.env.user.company_id.id,
                'user_id':self.env.user.id,
                'picking_state':'draft',
                'application':'sale_order_response',
                'export_qty':'0',
                'processed_qty':str(qty),
                'is_mismatch_detail':False if product_id else True,
                'skip_line':True,
                'create_date':datetime.now(),
                'operation_type':'export',
                'price':unit_price,
            }
            res = self.job_id.transaction_log_ids.create(avc_transaction_log_val)
            self.export_avc_line_id.append(res)
        
        
        po_ack_file_string = po_ack_file_string + "UNS+S'"
        total_segment += 1
        
        po_ack_file_string = po_ack_file_string + "CNT+2:%s'"%(str(line_no))
        total_segment += 1
        
        seq = self.env['ir.sequence'].get('amazon.edi.ship.message.trailer')
        po_ack_file_string = po_ack_file_string + "UNT+%s+%s'"%(str(total_segment), str(seq))
        po_ack_file_string = po_ack_file_string + "UNZ+1+%s'"%(str(seq_interchange))
        
        output = StringIO()
        result=base64.b64encode(po_ack_file_string.encode())
        output.write(po_ack_file_string)
        output.seek(0)
        file_order_ship.write(output.read().encode())
        file_order_ship.close()
      
        filename = "%s_%s.%s"%(vendor_id.po_ack_file_export_prefix,self.sale_id.amazon_edi_order_id,vendor_id.vendor_code)
        
        upload_file_name = '%s_%s_%s_%s_%s_%s_%s_%s.%s' % (
            vendor_id.po_ack_file_export_prefix,self.sale_id.amazon_edi_order_id, datetime.now().day, datetime.now().month, datetime.now().year, datetime.now().hour,
            datetime.now().minute, datetime.now().second,vendor_id.vendor_code)
        vals = {
            'name':upload_file_name,
            'datas':result,
            'datas_fname':upload_file_name,
            'res_model':'avc.file.transaction.log',
            'type':'binary',
            'res_id':self.job_id.id,
        }
        self.job_id.write({'filename':upload_file_name})
        attachment = self.env['ir.attachment'].create(vals)
        self.job_id.message_post(body=_("<b>Sale Order Acknowledgement File</b>"), attachment_ids=attachment.ids)
        connection_id = False
        if vendor_id.is_production_environment:
            ftp_server_id = vendor_id.production_ftp_connection
            directory_id = vendor_id.production_po_ack_directory_id
        else :
            ftp_server_id = vendor_id.test_ftp_connection
            directory_id = vendor_id.test_po_ack_directory_id
        with vendor_id.get_edi_sending_interface(ftp_server_id,directory_id) \
                as edi_interface:
            edi_interface.push_to_ftp(filename, file_order_ship.name)
        self.sale_id.write({'amazon_order_ack_uploaded':True})
        self.write({'po_ack_uploaded' : True})
        for lines in self.export_avc_line_id:
            lines.write({'filename':upload_file_name})
        return True

    @api.multi
    def resend_po_ack(self):
        """
        USE: While user want to resend purchase order acknowledgement at that time this method call,
        form this method directly export_po_ack() called and that method generate purchase order acknowledgement
        file and send it to amazon vendor central
        :return: export_po_ack()
        """
        return self.export_po_ack()
    
    
    @api.multi
    def get_package_qty(self,packages):
        total_qty = 0
        for package in packages:
            move_lines = package.with_context({'picking_id' : self.id}).current_picking_move_line_ids_ept
            qty = sum(move_lines.mapped('qty_done'))
            total_qty = total_qty + qty
        return total_qty

#     @api.multi
#     def get_package_qty(self,packages):
#         total_qty = 0
#         stock_move_obj = self.env['stock.move.line']
#         for package in packages:
#             move_lines = package.with_context({'picking_id' : self.id}).quant_ids
#             move_line_ids = stock_move_obj.search([('id','in',move_lines.ids)])
#             qty = sum(move_line_ids.mapped('qty_done'))
#             total_qty = total_qty + qty
#         return total_qty
    
    
    @api.multi
    def send_routing_request(self):
        file_routing_request = NamedTemporaryFile(delete=False)
        package_ids = self.package_ids
        route_info_file_string=""
        total_segment = 0
        message_info ={
                       'sender_id' : self.sale_id.sender_id,
                       'recipient_id' : self.sale_id.recipient_id,
                       'supplier_id' : self.sale_id.supplier_id,
                       'delivery_party_id' : self.sale_id.delivery_party_id,
                       'country_code' : self.sale_id.country_code,
                       'buyer_address' : self.sale_id.buyer_address,
                       'buyer_id' : self.sale_id.buyer_id,
                       }
        
        free_text = self.goods_description if self.goods_description != '' else 'Hazardous materials'
        free_text = free_text.replace('_', ' ')
        
        seq_interchange = self.env['ir.sequence'].get('amazon.edi.routing.transaction')
        seq = self.env['ir.sequence'].get('amazon.edi.ship.message.trailer')
        bol_number_seq = self.env['ir.sequence'].get('amazon.edi.bol.number')
        bol_number = self.sale_id and self.sale_id.vendor_id and self.sale_id.vendor_id.supplier_id + bol_number_seq
        now = datetime.strptime(str(datetime.now()), '%Y-%m-%d %H:%M:%S.%f')
        date_now = now.strftime("%Y%m%d")
        time_now = now.strftime("%H%M")
        
        delivery_date = self.scheduled_date
        #delivery_date = datetime.strptime(delivery_date ,'%Y-%m-%d %H:%M:%S' )
        delivery_date = delivery_date.strftime("%Y%m%d")
        
        total_qty = self.get_package_qty(package_ids)
        total_weight = self.gross_weight
        total_volume = self.gross_volume
        
        route_info_file_string = route_info_file_string + "UNB+UNOC:2+%s:%s+%s:%s+%s:%s+%s+++++EANCOM'"%(message_info.get('recipient_id'),self.vendor_id.vendor_qualifier,message_info.get('sender_id'),self.vendor_id.amazon_qualifier,date_now,time_now,seq_interchange)
        total_segment += 1
        
        route_info_file_string = route_info_file_string + "UNH+1+IFTMBF:D:01B:UN:EAN003'"
        total_segment +=1
        
        route_info_file_string = route_info_file_string + "BGM+335+%s'"%(bol_number_seq)
        total_segment +=1
        
        route_info_file_string = route_info_file_string + "DTM+137:%s%s:203'"%(date_now, time_now)
        total_segment +=1
        
        #NOTE: FTX+AAA has more option, here static 'Hazardous materials' is setted.
        route_info_file_string = route_info_file_string + "FTX+AAA+++%s'"%(free_text)
        total_segment +=1
        
        route_info_file_string = route_info_file_string + "RFF+BN:DES5A%s'"%(self.sale_id.amazon_edi_order_id)
        total_segment +=1
        
        route_info_file_string = route_info_file_string + "DTM+10:%s'"%(delivery_date)
        total_segment +=1
        
        route_info_file_string = route_info_file_string + "RFF+ON:%s:1'"%(self.sale_id.amazon_edi_order_id)
        total_segment +=1
        
        route_info_file_string = route_info_file_string + "RFF+BM:%s'" % (bol_number)
        total_segment += 1
        
        route_info_file_string = route_info_file_string + "NAD+SF+%s::9++%s+%s+%s++%s+%s'"%(message_info.get('supplier_id'), self.env.user.company_id.name, self.env.user.company_id.street or '', self.env.user.company_id.city or '', self.env.user.company_id.zip, self.env.user.company_id.country_id.code)
        total_segment +=1
        
        route_info_file_string = route_info_file_string + "NAD+ST+%s::9+++++++%s'"%(message_info.get('delivery_party_id',''),message_info.get('country_code',''))
        total_segment +=1
        
        route_info_file_string = route_info_file_string + "GID+1+0+%s:CT'"%(total_qty)
        total_segment +=1
        
        route_info_file_string = route_info_file_string + "HAN+3'"
        total_segment +=1
        
        route_info_file_string = route_info_file_string + "MEA+AAE+G+KGM:%s'"%(total_weight)
        total_segment +=1
        
        route_info_file_string = route_info_file_string + "MEA+AAE+AAW+MTQ:%s'"%(total_volume)
        total_segment +=1
      
        route_info_file_string = route_info_file_string  + "UNT+%s+%s'"%(total_segment,str(seq))
        route_info_file_string = route_info_file_string  + "UNZ+1+%s'"%(seq_interchange)
        
        output = StringIO()
        result=base64.b64encode(route_info_file_string.encode())
        output.write(route_info_file_string)
        output.seek(0)
        file_routing_request.write(output.read().encode())
        file_routing_request.close()
        
        vendor_id = self.sale_id.vendor_id
        
        filename = "%s_%s.%s" %(vendor_id.route_request_file_export_prefix,self.sale_id.amazon_edi_order_id,vendor_id.vendor_code)
        upload_file_name = '%s_%s_%s_%s_%s_%s_%s_%s.%s'%(vendor_id.route_request_file_export_prefix,self.sale_id.amazon_edi_order_id,datetime.now().day,datetime.now().month,datetime.now().year,datetime.now().hour,datetime.now().minute,datetime.now().second,vendor_id.vendor_code)

        avc_file_process_job_vals = {
            'message':'Routing Request Exported',
            'vendor_id':vendor_id.id,
            'filename':upload_file_name,
            'application':'routing_request',
            'operation_type':'export',
            'create_date':datetime.now(),
            'company_id':vendor_id.company_id.id or False,
            'sale_order_id':self.sale_id.id,
        }
        job_id = self.env['avc.file.transaction.log'].create(avc_file_process_job_vals)

        vals = {
            'name':upload_file_name,
            'datas':result,
            'datas_fname':upload_file_name,
            'res_model':'avc.file.transaction.log',
            'type':'binary',
            'res_id':job_id.id,
        }
        
        attachment = self.env['ir.attachment'].create(vals)   
        job_id.write({'attachment_id' : attachment.id})  
        job_id.message_post(body=_("<b>Routing Request File </b>"),attachment_ids=attachment.ids)
        connection_id = False
        if vendor_id.is_production_environment:
            ftp_server_id = vendor_id.production_ftp_connection
            directory_id = vendor_id.production_route_req_directory_id
        else :
            ftp_server_id = vendor_id.test_ftp_connection
            directory_id = vendor_id.test_po_ack_directory_id
        with vendor_id.get_edi_sending_interface(ftp_server_id,directory_id) \
                as edi_interface:
            edi_interface.push_to_ftp(filename, file_routing_request.name)
        self.write({'route_request_send' : True,'bol_number' : bol_number})
        return True
        
        
        
    @api.multi
    def receive_routing_request(self):
        ctx = self._context.copy() or {}
        vendor_id = self.sale_id and self.sale_id.vendor_id
        for vendor in vendor_id:
            self.job_id = None
            self.filename = None
            self.server_filename = None
            self.export_avc_line_id = []
            
            filenames_dict ={}
            
            file_to_delete = []
            connection_id = False
            if vendor.is_production_environment:
                ftp_server_id = vendor.production_ftp_connection
                directory_id = vendor.production_route_info_drectory_id
            else :
                ftp_server_id = vendor.test_ftp_connection
                directory_id = vendor.test_route_info_drectory_id
                                                  
            with vendor.get_edi_receive_interface(ftp_server_id,directory_id) \
                            as edi_interface:
                # `filenames` contains a list of filenames to be imported 
                filenames_dict = edi_interface.pull_from_ftp(vendor.route_info_file_import_prefix) 
                        
            for server_filename, filename in filenames_dict.items():
                
                with open(filename) as file:
                    self.filename = filename
                    self.server_filename = server_filename
                    ctx.update({'filename':server_filename})
                    self.process_file_and_prapare_routing(vendor,file)
                file_to_delete.append(server_filename)   
                
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
                    
                    self.job_id.message_post(body=_("<b>Routing Instruction file imported</b>"),attachment_ids=attachment.ids)
                    
                    if file_to_delete:
                        with vendor.get_edi_receive_interface(ftp_server_id,directory_id) \
                                    as edi_interface:
                            edi_interface.sftp_client.chdir(edi_interface.download_dir)
                            for filename in file_to_delete:
                                edi_interface.delete_from_ftp(filename)
        return True
    
    
    @api.multi 
    def process_file_and_prapare_routing(self,vendor,file):
        """
        Use to Process Route instruction file
        @param file : EDI file of Route Instruction
        """
        sale_order_obj = self.env['sale.order']
        avc_file_log_obj = self.env['avc.file.transaction.log']
        total_segment = 0
        ri_info = {}
        package_line_info = {}
        package_number = 0
        for segment in csv.reader(file,delimiter="'",quotechar='|'):
            for seg  in segment:
                if seg.startswith('UNB+UNOC') or seg.startswith('UNB+UNOA'):
                    header = seg.split("+")
                    ri_info.update({'sender_id':header[2][:-3], 'recipient_id':header[3][:-3]})
                    total_segment += 1
                    continue

                elif seg.startswith('UNH'):
                    msg_type = seg.split("+")
                    msg_type = msg_type[2].split(":")[0] if len(msg_type)>2 else ''
                    ri_info.update({'message_type' : msg_type})
                    total_segment +=1
                    continue

                elif seg.startswith('BGM+'):
                    order_name = seg.split("+")
                    order_name = order_name[2] if len(order_name) >= 3 else ''
                    ri_info.update({'order_name':order_name})
                    total_segment +=1
                    continue

                elif seg.startswith('DTM+137'):
                    date_seg = seg.split(":")
                    date_order = datetime.strptime(date_seg[1], '%Y%m%d')
                    ri_info.update({'date_order':date_order})
                    total_segment +=1
                    continue

                elif seg.startswith('FTX+LOI'):
                    loading_instruction = seg.split("+")
                    loading_instruction = loading_instruction[4].split(":")
                    ri_info.update({'load_type':loading_instruction[0],'load_value':loading_instruction[1]})
                    total_segment +=1
                    continue

                elif seg.startswith('RFF+BN'):
                    booking_reference = seg.split(":")
                    ri_info.update({'booking_reference':booking_reference[1]})
                    total_segment += 1
                    continue

                elif seg.startswith('DTM+10'):
                    shipment_req_date = seg.split(":")
                    ship_req_date = datetime.strptime(shipment_req_date[1], '%Y%m%d')
                    ri_info.update({'shipment_req_date':ship_req_date})
                    total_segment += 1
                    continue

                elif seg.startswith('DTM+200'):
                    pick_up_date_time = seg.split(":")
                    pick_up_date_time = datetime.strptime(pick_up_date_time[1], '%Y%m%d%H%M')
                    ri_info.update({'pick_up_date_time':pick_up_date_time})
                    total_segment += 1
                    continue

                elif seg.startswith('RFF+ACD'):
                    amazon_ref_number = seg.split(":")
                    ri_info.update({'amazon_ref_number':amazon_ref_number[1]})
                    total_segment += 1
                    continue

                elif seg.startswith('RFF+ON'):
                    amazon_order_number = seg.split(":")
                    order_list = ri_info.get('amazon_order_number',[])
                    order_list.append(amazon_order_number[1])
                    ri_info.update({'amazon_order_number':order_list})
                    total_segment += 1
                    continue

                elif seg.startswith('RFF+BM'):
                    bill_ref_number = seg.split(":")
                    ri_info.update({'bill_ref_number':bill_ref_number[1]})
                    total_segment += 1
                    continue

                elif seg.startswith('NAD+CA'):
                    transport_info = seg.split("+")
                    scac_id = (transport_info[2].split(":"))[0]
                    ri_info.update({'scac_id':scac_id,'carrier_name':transport_info[4],})
                    total_segment += 1
                    continue

                elif seg.startswith('CTA+CA'):
                    carrier_contact_name = seg.split(":")
                    ri_info.update({'carrier_contact_name':carrier_contact_name[1]})
                    total_segment += 1
                    continue

                elif seg.startswith('COM+'):
                    if not ri_info.get('carrier_tel_number','') or not ri_info.get('carrier_email',''):
                        carrier_contact = seg.split("+")[1].split(":")
                        if carrier_contact[1] == 'TE':
                            ri_info.update({'carrier_tel_number':carrier_contact[0]})
                        if carrier_contact[1] == 'EM':
                            ri_info.update({'carrier_email':carrier_contact[0]})
                        total_segment += 1
                        continue

                elif seg.startswith('NAD+SF'):
                    ship_from_info = seg.split("+")
                    address_info = {}
                    if ship_from_info[2].split(':')[1] == 9:
                        address_info.update({'warehouse_gln_number':ship_from_info[2].split(':')[0]  or ''})
                    elif ship_from_info[2].split(':')[1] == 92:
                        address_info.update({'warehouse_gln_number_by_amazon':ship_from_info[2].split(':')[0]  or ''})

                    address_info.update({
                        'company_name':ship_from_info[4] or '',
                        'street':ship_from_info[5] or '',
                        'city':ship_from_info[6] or '',
                        'zip':ship_from_info[8] or '',
                        'country_code':ship_from_info[9] or '',
                    })
                    ri_info.update({'ship_from_address':address_info})
                    total_segment += 1
                    continue

                elif seg.startswith('CTA+SU'):
                    supplier_contact_name = seg.split(":")
                    ri_info.update({'supplier_contact_name':supplier_contact_name[1]})
                    total_segment += 1
                    continue

                elif seg.startswith('COM+'):
                    if ri_info.get('carrier_tel_number',''):
                        supplier_contact = seg.split("+")[1].split(":")
                        if supplier_contact[1] == 'TE':
                            ri_info.update({'supplier_tel_number':supplier_contact[0]})
                        if supplier_contact[1] == 'EM':
                            ri_info.update({'supplier_email':supplier_contact[0]})
                        total_segment += 1
                        continue

                elif seg.startswith('NAD+ST'):
                    ship_to = seg.split("+")
                    ri_info.update({'ship_to_gln_number':ship_to[2][:-3],'ship_to_country_code':ship_to[9]})
                    total_segment += 1
                    continue

                elif seg.startswith('CTA+RD'):
                    dock_info = seg.split(":")
                    ri_info.update({'receiving_dock_contact_name':dock_info[1]})
                    total_segment += 1
                    continue

                elif seg.startswith('GID+'):
                    package_number += 1
                    package_line_info.update({'Line_' + str(package_number):{}})
                    package_info = seg.split("+")
                    if package_info[2] == '0':
                        package_line_info['Line_' + str(package_number)].update({'cartons':package_info[3][:-3]})
                    else:
                        if package_info[2].split(":")[1] == '201':
                            package_line_info['Line_' + str(package_number)].update({'standard_pallets':package_info[2][:-4]})
                        elif package_info[2].split(":")[1] == 'PX':
                            package_line_info['Line_' + str(package_number)].update({'non_standard_pallets':package_info[2][:-3]})
                    total_segment += 1
                    continue

                elif seg.startswith('HAN+3'):
                    package_line_info['Line_' + str(package_number)].update({'pallets_stackable':True})
                    total_segment += 1
                    continue

                elif seg.startswith('MEA+AAE'):
                    measurement = seg.split("+")
                    if measurement[2] == 'G':
                        package_line_info['Line_' + str(package_number)].update({'gross_weight':measurement[3][4:]})
                    elif measurement[2] == 'AAW':
                        package_line_info['Line_' + str(package_number)].update({'gross_volume':measurement[3][4:]})
                    total_segment += 1
                    continue

                elif seg.startswith('UNT+'):
                    unique_ref = seg.split("+")
                    ri_info.update({'unique_ref':unique_ref[1]})
                    total_segment += 1
                    continue

                elif seg.startswith('UNZ+'):
                    total_line = seg.split("+")
                    total_line = total_line[2]
                    #if int(total_line) != total_segment:
                    #    raise osv.except_osv(_('Error'), _('Order Line not integrated properly, Please Check order line data in file.'))
                    continue
        if not vendor.supplier_id == ri_info.get('recipient_id',''):
            raise osv.except_osv(_('Error'),_('Mismatch Vendor ID'))
        sale_order = sale_order_obj.search([('amazon_edi_order_id','in',ri_info.get('amazon_order_number',[])),('vendor_id','=',vendor.id)])
        if not sale_order:
            _logger.info('No Sale order found')
            raise osv.except_osv(_('Error'), _('No Sale Order Found %s'%(ri_info.get('amazon_order_number',[]))))
        
        avc_job_vals = {
                'message': 'Route Instruction Imported',
                'filename': self.server_filename,
                'vendor_id': vendor.id,
                'application' : 'routing_instruction',
                'operation_type' : 'import',
                'create_date' : datetime.now(),
                'company_id':vendor.company_id.id or False,
                'sale_order_id':sale_order.id,
            }
        
        self.job_id = avc_file_log_obj.create(avc_job_vals)
        
        stock_picking_vals = {
            'routing_instruction_received':True,
            'additional_ref_number':ri_info.get('amazon_ref_number',''),
            'loading_type':ri_info.get('load_type',''),
            'loading_value':ri_info.get('load_value',''),
            'pickup_date':ri_info.get('pick_up_date_time',False),
            'carrier_scac_id':ri_info.get('scac_id',''),
            'carrier_name':ri_info.get('carrier_name',''),
            'booking_ref_number':ri_info.get('booking_reference',''),
        }
        
        res = self.write(stock_picking_vals)
        
        return res
    
#     @api.multi
#     def button_validate(self):                                                               
#     
    
    @api.multi
    def send_advance_shipment_notice(self):
        sale_order_obj = self.env['sale.order']
        vendor = self.sale_id.vendor_id
        order = self.sale_id
        if not vendor:
            raise Warning("Vendor is not exist in sale order")
        bol_number = self.bol_number
        if not bol_number:
            bol_number_seq = self.env['ir.sequence'].get('amazon.edi.bol.number')
            bol_number = self.sale_id and self.sale_id.vendor_id and self.sale_id.vendor_id.supplier_id + bol_number_seq
        self.write({'bol_number' : bol_number})
        order_info = {
                'bol_number':self.bol_number,
                'order_name':order.amazon_edi_order_id,
                'date_done': self.scheduled_date,
                'sale_order_id':order.id,
                'sale_order_name':order.name,
                'warehouse_gln_number':order.warehouse_id.gln_number,
                'zipcode':order.warehouse_id.partner_id.zip,
                'country_code':order.warehouse_id.partner_id.country_id.code,
                'mode_of_transport':self.mode_of_transport or '30+31',
                'sscc_code':self.sscc_code,
            }
        
        if self.carrier_type == 'wepay':
            order_info.update({'carrier_name':self.carrier_name,
                            'carrier_reference_number':self.carrier_scac_id,
                            'aditional_ref_number':self.additional_ref_number,})
        elif self.carrier_type == 'we_not_pay':
            if order.carrier_id:
                order_info.update({'carrier_name':order.carrier_id.name,'carrier_reference_number':order.carrier_id.carrier_reference_number})
        
        message_info ={
                       'sender_id' : order.sender_id,
                       'recipient_id' : order.recipient_id,
                       'supplier_id' : order.supplier_id,
                       'delivery_party_id' : order.delivery_party_id,
                       'country_code' : order.country_code,
                       'buyer_address' : order.buyer_address,
                       'buyer_id' : order.buyer_id,
                       'latest_date':order.max_delivery_date_ept or False,
                       'earliest_date':order.delivery_date_ept or False,
                       'warehouse_gln_number':order.warehouse_id.gln_number,
                       }
        
        self.prepare_advance_shipment_notice_file(vendor,order,order_info,message_info)
        
    @api.multi
    def prepare_package_info(self,package_ids):
        sale_order_line_obj = self.env['sale.order.line']
        no_of_pallet = 0
        no_of_package = 0
        order_line_info = {}
        for package in package_ids:
            if package.package_type == 'pallet' :
                no_of_pallet = no_of_pallet + 1
            if package.package_type == 'carton' :
                no_of_package = no_of_package + 1
            stock_move_line_ids = package.with_context({'picking_id' : self.id}).current_picking_move_line_ids_ept
            for stock_move_line in stock_move_line_ids:
                order_line = {
                        'amazon_edi_code' : stock_move_line.move_id.sale_line_id.amazon_edi_line_code,
                        'amazon_edi_code_type' : stock_move_line.move_id.sale_line_id.amazon_edi_line_code_type,
                        'qty_done' : stock_move_line.qty_done,
                        'product_id' : stock_move_line.product_id.id,
                        'sale_order_line_id' : stock_move_line.move_id.sale_line_id.id
                    }
                if stock_move_line.product_id.tracking == 'lot':
                    for quant in stock_move_line.result_package_id.quant_ids:
                        if quant.product_id.id == stock_move_line.product_id.id:
                            order_line.update({'expiry_date':quant.removal_date or '','lot_id':quant.lot_id.name or '' })
                #order_line_info.append(order_line)
                
                if order_line_info.get(package.name):
                    data = order_line_info.get(stock_move_line.result_package_id.name).get('package_lines')
                    data.append(order_line)
                    package_info = order_line_info.get(stock_move_line.result_package_id.name).get('package_info')
                    order_line_info.update({package.name:{'package_lines':data,'package_info':package_info}})
                else :
                    package_info = {
                          'height':package.packaging_id.height or 0,
                          'width':package.packaging_id.width or 0,
                          'length':package.packaging_id.length or 0,
                          'gross_weight':package.amazon_package_weight or 0,
                          'handling_instructions':package.handling_instructions or 'BIG'
                        }
                    order_line_info.update({package.name:{'package_lines':[order_line],'package_info':package_info}})
        return order_line_info,no_of_pallet,no_of_package
        
    @api.multi
    def prepare_advance_shipment_notice_file(self,vendor,order,order_info,message_info):
        transaction_line_obj = self.env['avc.transaction.log.line']
        transaction_lines = []
        file_asn_notice = NamedTemporaryFile(delete=False)
        total_segment = 0
        file_asn_string = ""
        package_ids = self.package_ids
        package_line_info,no_of_pallet,no_of_package = self.prepare_package_info(package_ids)
        
        seq = self.env['ir.sequence'].get('amazon.edi.order.dispatch.advice')
        seq_interchange = self.env['ir.sequence'].get('amazon.edi.ship.message.trailer')

        file_asn_string = file_asn_string + "UNB+UNOC:2+%s:%s+%s:%s+%s:%s+%s+++++EANCOM'"%(message_info.get('recipient_id',False),vendor.vendor_qualifier,message_info.get('sender_id',False),vendor.amazon_qualifier,time.strftime("%y%m%d"),time.strftime("%H%M"),str(seq_interchange))
        total_segment +=1
        file_asn_string = file_asn_string + "UNH+%s+DESADV:D:96A:UN:EAN005'"%(str(seq))
        total_segment +=1
        file_asn_string = file_asn_string + "BGM+351+%s+9'"%("DES"+order_info.get('order_name',''))
        total_segment +=1
        
        #date_done = datetime.strptime(order_info.get('date_done'), '%Y-%m-%d %H:%M:%S')
        date_done = order_info.get('date_done')
        date_done = datetime.strftime(date_done,"%Y%m%d")
        #date_arrival = datetime.strptime(order_info.get('date_done'), '%Y-%m-%d %H:%M:%S') + relativedelta(days=vendor.order_dispatch_lead_time)
        date_arrival = order_info.get('date_done') + relativedelta(days=vendor.order_dispatch_lead_time) 
        date_arrival = datetime.strftime(date_arrival,"%Y%m%d")
        
        file_asn_string = file_asn_string + "DTM+11:%s:102'"%(date_done)
        total_segment +=1
        file_asn_string = file_asn_string + "DTM+132:%s:102'"%(date_arrival)
        total_segment +=1
        file_asn_string = file_asn_string + "DTM+137:%s:102'"%(time.strftime("%Y%m%d"))
        total_segment +=1
        file_asn_string = file_asn_string + "RFF+BM:%s'"% (order_info.get('bol_number',''))
        total_segment +=1
        file_asn_string = file_asn_string + "RFF+ON:%s'"% (order_info.get('order_name', ''))
        total_segment +=1
        file_asn_string = file_asn_string + "RFF+CN:%s'"% (order_info.get('carrier_reference_number',''))
        total_segment +=1
        file_asn_string = file_asn_string + "RFF+ACD:%s'" % (order_info.get('aditional_ref_number', ''))
        total_segment +=1
        # file_asn.write("""DTM+171:%s:102'"""%(date_arrival))
        # total_segment +=1
        if self.carrier_type == 'wepay':
            file_asn_string = file_asn_string + "NAD+CA+SCAC'"
            total_segment +=1
        file_asn_string = file_asn_string + "NAD+DP+%s::9+++++++%s'" % (message_info.get('delivery_party_id', ''), message_info.get('country_code', ''))
        total_segment += 1
        file_asn_string = file_asn_string + "NAD+SU+%s::9'" % (message_info.get('supplier_id', ''))
        total_segment += 1
        file_asn_string = file_asn_string + "NAD+SF+%s::9++++++%s+%s'"%(message_info.get('warehouse_gln_number',''),message_info.get('zipcode',''),message_info.get('country_code',''))
        total_segment +=1
        file_asn_string = file_asn_string + "TDT+20++%s'" % (str(order_info.get('mode_of_transport','')))
        total_segment +=1
        file_asn_string = file_asn_string + "CPS+1'"  # Define Entire shipment and represents the highest hierarchical level
        total_segment +=1
        #NOTE : PAC+X++201 and PAC+X++PK tags are use to display total count of pallets
        #Still pallets configuration not done so static 0 is setted in pallets count.
        # Need to check this : this is remaining
        file_asn_string = file_asn_string + "PAC+%s++201'"%(str(no_of_pallet))  # Number of pallets
        total_segment +=1
        file_asn_string = file_asn_string + "PAC+%s++PK'"%(str(no_of_package))  # Number of carton in One shipment
        total_segment +=1
        
        package_number = 0
        cnt_vals = 0.0
        line_no = 0
        
        for package,value in package_line_info.items():
            package_info = value.get('package_info',{})
            order_lines =value.get('package_lines',{})
            
            package_number += 1
            file_asn_string = file_asn_string + "CPS+%s+1'"%(str(package_number))  # First packing unit
            total_segment +=1
            file_asn_string = file_asn_string + "PAC+1+:52+PK'"
            total_segment +=1
            file_asn_string = file_asn_string + "MEA+PD+LN+CMT:%s'" % (str(package_info.get('length')))
            total_segment += 1
            file_asn_string = file_asn_string + "MEA+PD+WD+CMT:%s'" % (str(package_info.get('width')))
            total_segment += 1
            file_asn_string = file_asn_string + "MEA+PD+HT+CMT:%s'" % (str(package_info.get('height')))
            total_segment += 1
            file_asn_string = file_asn_string + "MEA+PD+AAB+KGM:%s'" % (str(package_info.get('gross_weight')))
            total_segment += 1
            file_asn_string = file_asn_string + "HAN+%s'" % (package_info.get('handling_instructions'))
            total_segment +=1
            file_asn_string = file_asn_string + "PCI+33E'"
            total_segment +=1
            file_asn_string = file_asn_string + "GIN+BJ+%s'"%(order_info.get('sscc_code'))
            total_segment +=1
            for line in order_lines:
                line_no += 1
                if line.get('amazon_edi_code_type') == 'barcode' :
                    file_asn_string = file_asn_string + "LIN+%s+5+%s:EN'"%(str(line_no),line.get('amazon_edi_code'))
                    total_segment += 1
                if line.get('amazon_edi_code_type') == 'sku':
                    file_asn_string = file_asn_string + "LIN+%s'"%(str(line_no))
                    total_segment +=1
                    file_asn_string = file_asn_string + "PIA+5+%s:SA'"%(line.get('amazon_edi_code',''))
                    total_segment +=1
                file_asn_string = file_asn_string + "QTY+12:%s'"%(str(line.get('qty_done',0)))
                total_segment += 1
                cnt_vals += line.get('product_qty',0)
                file_asn_string = file_asn_string + "RFF+ON:%s'" % (order_info.get('order_name', ''))
                total_segment += 1
                if line.get('expiry_date',''):
                    expory_date = datetime.strftime(datetime.strptime(line.get('expiry_date'), '%Y-%m-%d %H:%M:%S'),"%Y%m%d")
                    file_asn_string = file_asn_string + "PCI+17'"
                    total_segment += 1
                    file_asn_string = file_asn_string + "DTM+36:%s:102'" % (expory_date)
                    total_segment += 1
                    file_asn_string = file_asn_string + "GIN+BX+%s'" % (str(line.get('lot_id',0)))
                    total_segment += 1
                avc_transaction_log_val = {
                            'message':'Sale Order Line Created',
                            'remark':'sale order name %s'%(self.sale_id.name or ''),
                            'sale_order_id':order_info.get('sale_order_id',False),
                            #'job_id':self.job_id.id,
                            'sale_order_line_id' : line.get('sale_order_line_id'),
                            'picking_id':False,
                            'product_id':line.get('product_id',False),
                            'package_id':False,
                            'company_id':vendor.company_id.id or False,
                            'user_id':self.env.user.id,
                            'picking_state':self.state,
                            'application':'sale_order_despatch_advice',
                            'export_qty':str(line.get('qty_done',0)),
                            'processed_qty':str(line.get('qty_done',0)),
                            'create_date':datetime.now(),
                            'operation_type':'export',
                            }
                res = transaction_line_obj.create(avc_transaction_log_val)
                transaction_lines.append(res.id)
        
        file_asn_string = file_asn_string + "UNT+%s+%s'"%(str(total_segment),str(seq))
        file_asn_string = file_asn_string + "UNZ+1+%s'"%(str(seq_interchange))
        
        output = StringIO()
        result=base64.b64encode(file_asn_string.encode())
        output.write(file_asn_string)
        output.seek(0)
        file_asn_notice.write(output.read().encode())
        file_asn_notice.close()
        
        filename = "%s_%s.%s" %(vendor.asn_file_export_prefix,self.sale_id.amazon_edi_order_id,vendor.vendor_code)
        upload_file_name = '%s_%s_%s_%s_%s_%s_%s_%s.%s'%(vendor.asn_file_export_prefix,self.sale_id.amazon_edi_order_id,datetime.now().day,datetime.now().month,datetime.now().year,datetime.now().hour,datetime.now().minute,datetime.now().second,vendor.vendor_code)

        avc_file_process_job_vals = {
            'message':'Shipment Notice Exported ',
            'vendor_id':vendor.id,
            'filename':upload_file_name,
            'application':'sale_order_despatch_advice',
            'operation_type':'export',
            'create_date':datetime.now(),
            'company_id':vendor.company_id.id or False,
            'sale_order_id':self.sale_id.id,
        }
        job_id = self.env['avc.file.transaction.log'].create(avc_file_process_job_vals)
        job_id.write({'transaction_log_ids' : [(6,0,transaction_lines)]})
        vals = {
            'name':upload_file_name,
            'datas':result,
            'datas_fname':upload_file_name,
            'res_model':'avc.file.transaction.log',
            'type':'binary',
            'res_id':job_id.id,
            
        }
        attachment = self.env['ir.attachment'].create(vals)   
        job_id.write({'attachment_id' : attachment.id})  
        job_id.message_post(body=_("<b>Advance Shipment Notice </b>"),attachment_ids=attachment.ids)
        connection_id = False
        if vendor.is_production_environment:
            ftp_server_id = vendor.production_ftp_connection
            directory_id = vendor.production_asn_directory_id
        else :
            ftp_server_id = vendor.test_ftp_connection
            directory_id = vendor.test_asn_directory_id
        with vendor.get_edi_sending_interface(ftp_server_id,directory_id) \
                as edi_interface:
            edi_interface.push_to_ftp(filename, file_asn_notice.name)
        self.write({'shipment_notice_send' : True})
        return True
    
    
    @api.multi
    def send_invoice_to_vendor_central(self):
        transaction_line_obj = self.env['avc.transaction.log.line']
        transaction_lines = []
        sale_order_obj = self.env['sale.order']
        avc_file_process_job_obj = self.env['avc.file.transaction.log']
        account_invoice_tax_obj = self.env['account.invoice.tax']
        self.job_id = None
        #batch = self.env['stock.picking.batch'].browse(self.id)
        invoice_ids = self.mapped('sale_id').mapped('invoice_ids')
        
           
        for invoice in invoice_ids:
            transaction_line_ids=[]
            invoice.write({'is_amazon_edi_invoice':True})
#                 if invoice.state in ['draft','cancel'] or invoice.exported_to_edi == True:
#                     continue
            count = 0 
            for lines in invoice.invoice_line_ids:
                if lines.product_id.type != 'service':
                    count +=1
            if count == 0:
                continue
            #NOTE: here taken 1st stock picking record based on thate record date of delivery set.
#                 date_deliver = stock_picking_ids[0].date_done
#                 if not date_deliver:
#                     raise osv.except_osv(_('Error'),
#                                          _("No delivery date found..!\nCheck %s's stock picking..! " % (order.name)))
#                 else:
#                     date_deliver = datetime.strptime(date_deliver, '%Y-%m-%d %H:%M:%S')
#                     date_deliver = date_deliver.strftime("%Y%m%d")
            #NOTE: here TAX RATE taken from account.invoice.tax where invoice_id is current record's invoice_id and first record's data are considered
            account_invoice_tax_id = account_invoice_tax_obj.search([('invoice_id','=',invoice.id)], limit = 1)
            invoice_tax_rate = account_invoice_tax_id.tax_id.amount or 0.0
            if not self.job_id:
                avc_file_process_job_values = {
                    'message': 'Invoice exported',
                    'vendor_id': invoice.invoice_line_ids[0].sale_line_ids[0].order_id.vendor_id.id,
                    'application' : 'invoice',
                    'operation_type' : 'export',
                    'create_date' : datetime.now(),
                    'company_id':invoice.invoice_line_ids[0].sale_line_ids[0].order_id.company_id.id,
                    'sale_order_id':invoice.invoice_line_ids[0].sale_line_ids[0].order_id.id,
                    }
                self.job_id = avc_file_process_job_obj.create(avc_file_process_job_values)
                
            message_info ={
                       'sender_id' : invoice.invoice_line_ids[0].sale_line_ids[0].order_id.sender_id,
                       'recipient_id' :invoice.invoice_line_ids[0].sale_line_ids[0].order_id.recipient_id,
                       'supplier_id' :invoice.invoice_line_ids[0].sale_line_ids[0].order_id.supplier_id,
                       'delivery_party_id' :invoice.invoice_line_ids[0].sale_line_ids[0].order_id.delivery_party_id,
                       'country_code' : invoice.invoice_line_ids[0].sale_line_ids[0].order_id.country_code,
                       'buyer_address' :invoice.invoice_line_ids[0].sale_line_ids[0].order_id.buyer_address,
                       'buyer_id' :invoice.invoice_line_ids[0].sale_line_ids[0].order_id.buyer_id,
                       }    
            #order_name = invoice.invoice_line_ids[0].sale_line_ids[0].order_id.amazon_edi_order_id
            order =  invoice.invoice_line_ids[0].sale_line_ids[0].order_id
            #date_deliver = order.picking_ids[0].date_done
            date_deliver = self.date_done
            #date_deliver = datetime.strftime(date_deliver,"%Y%m%d")

            if not date_deliver:
                raise osv.except_osv(_('Error'),
                                     _("No delivery date found..!\nCheck %s's stock picking..! " % (order.name)))
            else:
                date_deliver = datetime.strftime(date_deliver,"%Y%m%d")

            
            if not order.sender_id or not order.recipient_id:
                raise osv.except_osv(_('Error'), _('Sender or recipient identifier not found.'))
            invoice_seq = self.env['ir.sequence'].get('amazon.edi.invoice.message.number')
            total_segment = 0
            send_file_invoice = NamedTemporaryFile(delete=False)
            file_invoice = "" 
            file_invoice = file_invoice + """UNB+UNOA:2+%s:%s+%s:%s+%s:%s+%s+++++EANCOM'"""%(order.recipient_id or '',order.vendor_id.vendor_qualifier,order.sender_id or '',order.vendor_id.amazon_qualifier,time.strftime("%y%m%d"),time.strftime("%H%M"),str(invoice_seq))
            total_segment +=1
            file_invoice = file_invoice + """UNH+1+INVOIC:D:96A:UN:EAN008'"""
            total_segment +=1
            inv_no = invoice.number and invoice.number[invoice.number.rfind('/')+1:] or ''
            file_invoice = file_invoice + """BGM+380+%s'"""%(str(inv_no))
            total_segment +=1
            file_invoice = file_invoice + """DTM+137:%s:102'"""%(time.strftime("%Y%m%d"))
            total_segment +=1
            file_invoice = file_invoice + """DTM+35:%s:102'"""%(date_deliver)
            total_segment +=1
            #Supplier Segment
            company_name = invoice.company_id and (invoice.company_id.name).replace("'","") or ''
            company_street = invoice.company_id and (invoice.company_id.street).replace("'","") or ("10 passage de l'industrie").replace("'","")
            company_city = invoice.company_id and (invoice.company_id.city).replace("'","") or ""
            company_zip = invoice.company_id and (invoice.company_id.zip).replace("'","") or ""
            country_code = invoice.company_id and invoice.company_id.country_id and invoice.company_id.country_id.code or "FR"  
            vat_reg_no = invoice.company_id and invoice.company_id.vat or '' # MGC(Supplier) VAT Number
            file_invoice = file_invoice + """NAD+SU+%s::9++%s+%s+%s++%s+%s'"""%(str(order.supplier_id),company_name,company_street,company_city,str(company_zip),country_code)
            total_segment +=1
            file_invoice =  file_invoice + """RFF+VA:%s'""" % (vat_reg_no)
            total_segment += 1
            file_invoice = file_invoice + """NAD+DP+%s::9+++++++%s'""" % (order.buyer_id,order.country_code)
            total_segment += 1
            #Invoice Segment
            iv_name = invoice.partner_id and (invoice.partner_id.name).replace("'","") or ''
            street = invoice.partner_id and (invoice.partner_id.street).replace("'","") or ''
            street2 = invoice.partner_id and (invoice.partner_id.street2).replace("'","") or ''
            city = invoice.partner_id and (invoice.partner_id.city).replace("'","") or ''
            zipcode = invoice.partner_id and invoice.partner_id.zip or ''
            country_code = invoice.partner_id and invoice.partner_id.country_id and invoice.partner_id.country_id.code or ''  
            file_invoice = file_invoice + """NAD+IV+%s::9++%s:%s+%s+%s++%s+%s'"""%(order.invoice_id,iv_name,street,street2,city,zipcode,country_code)
            total_segment +=1
            file_invoice = file_invoice + """RFF+VA:%s'""" % (order.vat_number or '')
            total_segment += 1
            file_invoice =file_invoice + """CUX+2:%s:4'"""%(order.currancy_code or '')
            total_segment +=1
            file_invoice = file_invoice + """PAT+1++5::D:30'""" #payment Term 30 days Net
            total_segment +=1
            #date_done = datetime.strptime(order.date_order, '%Y-%m-%d %H:%M:%S')
            #date_done = order.date_order
            date_done = order.date_order.strftime("%Y%m%d")
            file_invoice = file_invoice + """DTM+171:%s:102'"""%(date_done) #payment Term 30 days Net
            total_segment +=1
            
            line_no = 1
            tax_per = 0.0
            for line in invoice.invoice_line_ids:
                if line.product_id.type == 'service':
                    continue
                code = line.product_id and line.product_id.default_code or ''
                ean = line.product_id  and line.product_id.barcode or ''
                amazon_sku = line.product_id and line.product_id.amazon_sku or ''
                order_name = line.sale_line_ids.order_id.amazon_edi_order_id
                qty = line.quantity or 0.0
                subtotal = line.price_subtotal 
                price = line.price_unit
                tax_per = line.invoice_line_tax_ids and line.invoice_line_tax_ids[0] and (line.invoice_line_tax_ids[0].amount) or 0
                tax_amount = (price * tax_per) / 100
                tax_amount = "%.2f" % tax_amount
                if ean == amazon_sku:
                    file_invoice = file_invoice + """LIN+%s++%s:EN'"""%(str(line_no),amazon_sku)
                    total_segment +=1
                if amazon_sku == ean:
                    file_invoice = file_invoice +  """LIN+%s'""" % (str(line_no))
                    total_segment += 1
                    file_invoice = file_invoice + """PIA+5+%s:SA'"""%(str(amazon_sku))
                    total_segment +=1
                file_invoice = file_invoice + """QTY+47:%s'"""%(str(qty))
                total_segment +=1
                file_invoice = file_invoice + """MOA+203:%s:%s:4'"""%(str(subtotal), invoice.currency_id.name or 'EUR') #Line item amount
                total_segment +=1
                file_invoice = file_invoice + """PRI+AAA:%s:CT:NTP'"""%(str(price)) #Net Price Unit
                total_segment +=1
                file_invoice = file_invoice + """RFF+ON:%s'"""%(str(order_name)) #Order Name
                total_segment +=1
                file_invoice = file_invoice + """TAX+7+VAT+++:::%s'"""%(str(int(tax_per)))
                total_segment +=1
                file_invoice = file_invoice + """MOA+124:%s:%s:4'""" % (str(tax_amount), invoice.currency_id.name or 'EUR')
                total_segment += 1
                line_no +=1
                avc_transaction_log_val = {
                    'message':'Invoice Line Created',
                    'remark':'sale order id %s'%(order.id),
                    'sale_order_id':order.id,
                    'job_id':self.job_id.id,
                   # 'picking_id':stock_picking_ids[0].id or False,
                    'back_order_id':False,
                    'product_id':line.product_id.id,
                    'package_id':False,
                    'stock_inventory_id':False,
                    'company_id':order.company_id.id,
                    'user_id':self.env.user.id,
                    #'picking_state':stock_picking_ids[0].state,
                    'application':'invoice',
                    'export_qty':qty,
                    'processed_qty':qty,
                    'create_date':datetime.now(),
                    'operation_type':'export',
                    }
                  
                res = transaction_line_obj.create(avc_transaction_log_val)
                transaction_lines.append(res.id)
                  
            file_invoice = file_invoice + """UNS+S'"""
            total_segment +=1    
            file_invoice = file_invoice + """CNT+2:%s'"""%(str(line_no-1))
            total_segment +=1
            
            file_invoice = file_invoice + """MOA+77:%s:%s:4'"""%(str(invoice.amount_total),str(order.currancy_code)) #Whole Invoice Amount total with tax included
            total_segment +=1
            
            file_invoice = file_invoice + """TAX+7+VAT+++:::%s'"""%(str(int(invoice_tax_rate))) # Whole invoice Tax Rate
            total_segment +=1
            file_invoice = file_invoice + """MOA+124:%s:%s:4'"""%(str(invoice.amount_tax),str(order.currancy_code)) #Tax Amount
            total_segment +=1
            
            file_invoice = file_invoice +  """MOA+125:%s:%s:4'"""%(str(invoice.amount_untaxed),str(order.currancy_code)) #Untaxed Amount
            total_segment +=1
                
            file_invoice =  file_invoice + """UNT+%s+1'"""%(str(total_segment))
            file_invoice = file_invoice + """UNZ+1+%s'"""%(str(invoice_seq))
            
            out = StringIO()
            result=base64.b64encode(file_invoice.encode())
            out.write(file_invoice)
            out.seek(0)
            send_file_invoice.write(out.read().encode())
            send_file_invoice.close()  
                 
            
            filename = "ORDINVOIC_%s.txt" %(str(order_name))
            
            upload_file_name = '%s_%s_%s_%s_%s_%s_%s.mgc'%(filename,datetime.now().day,datetime.now().month,datetime.now().year,datetime.now().hour,datetime.now().minute,datetime.now().second)
            
#             avc_file_process_job_values = {
#                     'message': 'Invoice exported',
#                     'vendor_id': invoice.invoice_line_ids[0].sale_line_ids[0].order_id.vendor_id.id,
#                     'filename':upload_file_name,
#                     'application' : 'invoice',
#                     'operation_type' : 'export',
#                     'create_date' : datetime.now(),
#                     'company_id':invoice.invoice_line_ids[0].sale_line_ids[0].order_id.company_id.id,
#                     'sale_order_id':invoice.invoice_line_ids[0].sale_line_ids[0].order_id.id,
#                     }
#             job_id = self.env['avc.file.transaction.log'].create(avc_file_process_job_values)
            self.job_id.write({'transaction_log_ids' : [(6,0,transaction_lines)]})
    
            vals = {
                'name':upload_file_name,
                'datas':result,
                'datas_fname':upload_file_name,
                'res_model':'avc.file.transaction.log',
                'type':'binary',
                'res_id':self.job_id.id,
                }
            
            attachment = self.env['ir.attachment'].create(vals)   
            self.job_id.write({'attachment_id' : attachment.id})     
            self.job_id.message_post(body=_("<b>Invoice EDI file</b>"),attachment_ids=attachment.ids)
            
            connection_id = False
            if self.vendor_id.is_production_environment:
                ftp_server_id = invoice.invoice_line_ids[0].sale_line_ids[0].order_id.vendor_id.production_ftp_connection
                directory_id = invoice.invoice_line_ids[0].sale_line_ids[0].order_id.vendor_id.production_asn_directory_id
            else :
                ftp_server_id = invoice.invoice_line_ids[0].sale_line_ids[0].order_id.vendor_id.test_ftp_connection
                directory_id = invoice.invoice_line_ids[0].sale_line_ids[0].order_id.vendor_id.test_asn_directory_id            
            with invoice.invoice_line_ids[0].sale_line_ids[0].order_id.vendor_id.get_edi_sending_interface(ftp_server_id,directory_id) \
                        as edi_interface:
                edi_interface.push_to_ftp(filename, send_file_invoice.name)
             
            self.job_id.write({'filename':upload_file_name})
            for lines in transaction_line_ids:
                lines.write({'filename':upload_file_name})
            invoice.write({'exported_to_edi':True})
        return True
                
        