from odoo import models, fields, api, _
from odoo.osv import expression, osv
from odoo.exceptions import Warning, ValidationError
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

class amazon_vendor_instance(models.Model):
    _name = 'amazon.vendor.instance'
    _sql_constraints = [
        ('amazon_vendor_instance_unique', 'unique(name)',
         'The Amazon Vendor Instance Name must be unique!'),
    ]
    _description = 'Amazon Vendor Instance'
    
    @api.model
    def _get_stock_field_id(self):
        field = self.env['ir.model.fields'].search(
            [('model', '=', 'product.product'),
             ('name', '=', 'virtual_available')],
            limit=1)
        return field
    
    name = fields.Char("Vendor Name")
    country_id = fields.Many2one('res.country', string="Country")
    company_id = fields.Many2one('res.company', string='Company')
    journal_id = fields.Many2one('account.journal', string='Journal')
    #connection_type = fields.Selection([('test_connection','Test Connection'),('production_connection','Production Connection')], string = 'Connection Type')
    is_production_environment = fields.Boolean("Production Environment",default=False)
    #ftp_server_id = fields.Many2one('vendor.ftp.server',string="FTP server",help="FTP server for Import or Export file")
    amazon_edi_carrier_method = fields.Many2one('delivery.carrier', 'Amazon EDI Carrier')
    pricelist_id = fields.Many2one('product.pricelist',string='Pricelist')
    supplier_id = fields.Char(string='Supplier ID',help="Supplier ID is given by Amazon Vendor Central and all Purchase Order has this number as supplier id.\nHelp's to identify supplier.")
    order_dispatch_lead_time =  fields.Integer(string = "Order Lead Time", default = 1, help = "The average delay in days between the Routing Request send and ready for order shipment.")
    file_format_for_export = fields.Selection([('flat_file','Flat File'),('edi','EDI')],string = 'File Format for Export')
    delivery_type = fields.Selection([('wepay','WePay'),('we_not_pay','We not Pay')], string = 'Delivery Type')

    vendor_code = fields.Char('Vendor code')
    vendor_qualifier = fields.Char("Vendo Qualifier")
    amazon_qualifier = fields.Char("Amazon Qualifier",default="14")     

    
    mismatch_product = fields.Selection([('cancel', 'Cancel'), ('reject', 'Reject'), ('backorder', 'Backorder'), ],
                                        string='If Product not Found')
    
    #FTP configuration fields
    test_ftp_connection = fields.Many2one('vendor.ftp.server',string="Test FTP server")
    test_po_directory_id = fields.Many2one('ftp.server.directory.list',string="Test PO Import")
    test_po_ack_directory_id = fields.Many2one('ftp.server.directory.list',string="Test PO ACK ")
    test_route_req_directory_id = fields.Many2one('ftp.server.directory.list',string="PO Route Request")
    test_route_info_drectory_id = fields.Many2one('ftp.server.directory.list',string="Route info ")
    test_inv_cost_directory_id = fields.Many2one('ftp.server.directory.list',string="Inventory and cost ")
    test_invoice_directory_id = fields.Many2one('ftp.server.directory.list',string="PO Invoice")
    test_asn_directory_id = fields.Many2one('ftp.server.directory.list',string="Advance Shipment Notice")
    test_sale_report_directory_id = fields.Many2one('ftp.server.directory.list',string="Sale Report")
    
    production_ftp_connection = fields.Many2one('vendor.ftp.server',string="Production FTP server")
    production_po_directory_id = fields.Many2one('ftp.server.directory.list',string="PO Import")
    production_po_ack_directory_id = fields.Many2one('ftp.server.directory.list',string="PO ACK ")
    production_route_req_directory_id = fields.Many2one('ftp.server.directory.list',string="Route request ")
    production_route_info_drectory_id = fields.Many2one('ftp.server.directory.list',string="Route Info ")
    production_inv_cost_directory_id = fields.Many2one('ftp.server.directory.list',string="Inventory and Cost ")
    production_invoice_directory_id = fields.Many2one('ftp.server.directory.list',string="Invoice ")
    production_asn_directory_id = fields.Many2one('ftp.server.directory.list',string="Advance Shipment notice ")
    production_sale_report_directory_id = fields.Many2one('ftp.server.directory.list',string="Sale report")
        
    #PO import 
    #po_import_directory_id = fields.Many2one('ftp.server.directory.list',string="PO Import Directory")
    po_file_import_prefix = fields.Char('PO Import File Prefix')
    warehouse_id = fields.Many2one('stock.warehouse',string="Warehouse",help='Warehouse for Sale Order Import')
    team_id=fields.Many2one('crm.team', 'Sales Team',oldname='section_id')
    fiscal_position_id = fields.Many2one('account.fiscal.position', 'Fiscal Position')
    #PO ack
    #po_export_ack_directory_id = fields.Many2one('ftp.server.directory.list',string="PO Ack Export Directory")
    po_ack_file_export_prefix = fields.Char('PO Ack Export File Prefix')
    auto_confirm_sale_order = fields.Boolean("Auto Confirm Sale Order")
    auto_generate_po_ack = fields.Boolean("Auto Generate PO ACK")
    picking_policy = fields.Selection([('direct', 'Deliver each product when available'),('one', 'Deliver all products at once')],string='Shipping Policy', default='direct',)
    picking_policy_based_on = fields.Selection([('qty_on_hand', 'Quantity On Hand'),
                                                ('forecast_sale', 'Forecast Sale')], default="qty_on_hand",
                                               string="Partially Based On")
    
    so_customer_id = fields.Many2one('res.partner',string="Sale Order Partner")
    
    #Routing Request
    #route_request_export_directory_id = fields.Many2one('ftp.server.directory.list',string="Route Request Import Directory")
    route_request_file_export_prefix = fields.Char('Route Request File Prefix')
    
    #Routing Information
    #route_info_export_directory_id = fields.Many2one('ftp.server.directory.list',string="Route Info Export Directory")
    route_info_file_import_prefix = fields.Char('Route Info File Prefix')
    
    #Inventory and cost
    amazon_gln_number = fields.Char("Amazon GLN Number")
    #is_allow_stock_export_from_multi_warehouse = fields.Boolean("Stock export from Multi Warehouse")
    warehouse_ids = fields.Many2many('stock.warehouse',string="Warehouses",help="This warehouse will use for stock export if stock is available in multiple warehouse.\n Otherwise it take stock form Warehouse which is selected for Sale order")
    product_stock_field_id = fields.Many2one('ir.model.fields',string='Stock Field',default=_get_stock_field_id,domain="[('model', 'in', ['product.product', 'product.template']),('ttype', '=', 'float')]",
                help="Choose the field of the product which will be used for stock inventory updates.\nIf empty, Quantity Available is used.")
    #inventory_export_directory_id = fields.Many2one('ftp.server.directory.list',string="Inventory Export Directory")
    inventory_file_export_prefix = fields.Char('Inventory File Prefix')
    production_feed_key = fields.Char(string = 'FEED KEY')
    amazon_unb_id  = fields.Char(string = 'Amazon Unb')
    #include_forecast_incoming = fields.Boolean(string = "Include Forecast Incoming Quantity", help = "It will allow to send incoming product information in Inventory Report Message")
    
    #Invoice configuration
    journal_id = fields.Many2one('account.journal','Account Journal',help='Invoice is created in selected Journal')
    invoice_policy = fields.Selection([('order', 'Ordered quantities'),('delivery', 'Delivered quantities'),],string='Invoicing Policy')
    #invoice_export_directory_id = fields.Many2one('ftp.server.directory.list',string="Invoice Export Directory")
    invoice_file_export_prefix = fields.Char('Invoice File Prefix')
    
    #advance shipment notice
    #asn_export_directory_id = fields.Many2one('ftp.server.directory.list',string="Shipment Notice Export Directory")
    asn_file_export_prefix = fields.Char('Shipment Notice File Prefix')
    #sales report 
    #sales_report_directory_id = fields.Many2one('ftp.server.directory.list',string="Sales report Export Directory")
    sales_report_file_export_prefix = fields.Char('Sales report File Prefix')
    
    #count fields
    product_count = fields.Integer(string = "Products", compute = "_count_all")
    pending_po_count = fields.Integer(string = "Pending POs", compute = "_count_all")
    confirmed_po_count = fields.Integer(string = "Confirmed POs", compute = "_count_all")
    confirmed_picking_count = fields.Integer(string = "Waiting Availability", compute = "_count_all")
    assigned_picking_count = fields.Integer(string = "Ready to Transfer", compute = "_count_all")
    partially_available_picking_count = fields.Integer(string = "Partially Available", compute = "_count_all")
    done_picking_count = fields.Integer(string = "Transfered", compute = "_count_all")
    #open_invoice_count = fields.Integer(string = "Open Invoices")
    #close_invoice_count = fields.Integer(string = "Close Invoices")
    color = fields.Integer(string='Color Index')
    # crons
    auto_process_po = fields.Boolean(string='Auto Process Purchase Order?')
    auto_generate_po_ack = fields.Boolean(string='Auto Generate PO Ack?')
    auto_process_dispatch_advice = fields.Boolean(string="Auto Export Dispatch Advice?")
    auto_process_routing_instruction = fields.Boolean(string="Auto Process Routing Instruction?")
    auto_process_invoice = fields.Boolean(string="Auto Export Invoice?")
    auto_process_inventory = fields.Boolean(string="Auto Export Inventory?")
    auto_process_sales_report = fields.Boolean(string="Auto Import Sales Report?")
   
   
    @api.multi
    def toggle_prod_enviroment_value(self):
        """
        This will switch environment between production and pre-production.
        @return : True
        @author: Tejas Thakar on dated 06-June-2017
        """
        self.ensure_one()
        self.is_production_environment = not self.is_production_environment

    @api.multi
    def _count_all(self):
        sale_order_obj = self.env['sale.order']
        product_tmpl_obj = self.env['product.template']
        #product_obj = self.env['product.product']
        stock_picking_obj = self.env['stock.picking']
        product_tmpl_ids = product_tmpl_obj.search([('is_amazon_product','=',True)]).ids
        for instance in self:
            amazon_sale_order = sale_order_obj.search([('is_amazon_edi_order','=',True),('vendor_id','=',instance.id)]).ids
            pending_po = sale_order_obj.search([('is_amazon_edi_order','=',True),('vendor_id','=',instance.id),('state','in',['draft', 'sent', 'cancel'])]).ids
            confirmed_po = sale_order_obj.search([('is_amazon_edi_order','=',True),('vendor_id','=',instance.id),('state','not in',['draft', 'sent', 'cancel'])]).ids
            confirmed_picking = stock_picking_obj.search([('sale_id','in',amazon_sale_order),('state','in',['confirmed'])]).ids
            assigned_picking = stock_picking_obj.search([('sale_id','in',amazon_sale_order),('state','in',['assigned'])]).ids
            partially_available_picking = stock_picking_obj.search([('sale_id','in',amazon_sale_order),('state','in',['partially_available'])]).ids
            done_picking = stock_picking_obj.search([('sale_id','in',amazon_sale_order),('state','in',['done'])]).ids

            instance.product_count = len(product_tmpl_ids)
            instance.pending_po_count = len(pending_po)
            instance.confirmed_po_count = len(confirmed_po)
            instance.confirmed_picking_count = len(confirmed_picking)
            instance.assigned_picking_count = len(assigned_picking)
            instance.partially_available_picking_count = len(partially_available_picking)
            instance.done_picking_count = len(done_picking)
    
    @api.multi
    def check_test_ftp_server_connection(self):
        if self.test_ftp_connection:
            self.test_ftp_connection.do_test_connection()
        else :
            raise Warning("Please select FTP server first")
    
    @api.multi
    def check_production_ftp_server_connection(self):
        if self.production_ftp_connection:
            self.production_ftp_connection.do_test_connection()
        else :
            raise Warning("Please select FTP server first")

    # import sale order methods
    @api.multi
    def import_amazon_edi_order(self):
        file_datas = None
        self.env['sale.order'].import_sales_from_amazon_edi(self, file_data=file_datas)
        return True

    @api.multi
    def prepare_and_send_edi_inventory_message(self, args={}):
        product_template_obj = self.env['product.template']
        if args.get('vendor_id'):
            vendor_id = self.browse(args.get('vendor_id'))
            product_template_obj.prepare_and_send_edi_inventory_message(vendor_id=vendor_id,
                                                                        warehouse_for_stock=vendor_id.warehouse_for_stock)
        else:
            product_template_obj.prepare_and_send_edi_inventory_message(vendor_id=self,
                                                                        warehouse_for_stock=self.warehouse_for_stock)
        return True

    @api.multi
    def get_edi_receive_interface(self,ftp_server_id,direcotry_id):
        return AmazonEDIInterface(
            ftp_server_id.ftp_host + ':' + ftp_server_id.ftp_port,
            ftp_server_id.receive_ftp_user,
            None,
            ftp_server_id.ftp_key_location,
            download_dir=direcotry_id.path
            )
    
    @api.multi
    def get_edi_sending_interface(self,ftp_server_id,direcotry_id):
        return AmazonEDIInterface(
            ftp_server_id.ftp_host + ':' + ftp_server_id.ftp_port,
            ftp_server_id.sending_ftp_user,
            None,
            ftp_server_id.ftp_key_location,
            upload_dir=direcotry_id.path
            )

    @api.multi
    def import_sales_report(self):
        self.env['amazon.sales.report'].import_sales_report(vendor_id = self.id)
    
    
    @api.model
    def sync_amazon_po_from_cron(self,args={}):
        vendor_id = args.get('vendor_id')
        if vendor_id:
            vendor = self.browse(vendor_id)
            vendor.import_amazon_edi_order()
            
    @api.model
    def export_po_ack_from_cron(self,args={}):
        picking_obj = self.env['stock.picking']
        vendor_id = args.get('vendor_id')
        if vendor_id:
            vendor = self.browse(vendor_id)
            pickings = picking_obj.search([('sale_id.vendor_id','=',vendor.id),('is_amazon_edi_picking','=',True),('po_ack_uploaded','=',False),('state','not in',['cancel','done'])])
            for picking in pickings:
                picking.export_po_ack()
    @api.model
    def export_route_request_from_cron(self,args={}):
        picking_obj = self.env['stock.picking']
        vendor_id = args.get('vendor_id')
        if vendor_id:
            vendor = self.browse(vendor_id)
            pickings = picking_obj.search([('sale_id.vendor_id','=',vendor.id),('is_amazon_edi_picking','=',True),('po_ack_uploaded','=',True),('carrier_type','=','wepay'),('route_request_send','=',False),('state','not in',['cancel','done'])])
            for picking in pickings:
                picking.send_routing_request()
                
    @api.model
    def import_route_info_form_cron(self,args={}):
        picking_obj = self.env['stock.picking']
        vendor_id = args.get('vendor_id')
        if vendor_id:
            vendor = self.browse(vendor_id)
            pickings = picking_obj.search([('sale_id.vendor_id','=',vendor.id),('is_amazon_edi_picking','=',True),('carrier_type','=','wepay'),('route_request_send','=',True),('state','not in',['cancel','done'])])
            for picking in pickings:
                picking.receive_routing_request()
                
    @api.model
    def export_advance_shipment_notice_from_cron(self,args={}):
        vendor_id = args.get('vendor_id')
        picking_obj = self.env['stock.picking']
        if vendor_id:
            vendor = self.browse(vendor_id)
            pickings = []
            if vendor.delivery_type == 'wepay' :
                pickings = picking_obj.search([('sale_id.vendor_id','=',vendor.id),('carrier_type','=','wepay'),('is_amazon_edi_picking','=',True),('routing_instruction_received','=',True),('state','not in',['cancel','done'])])
            if vendor.delivery_type == 'we_not_pay':
                pickings = picking_obj.search([('sale_id.vendor_id','=',vendor.id),('carrier_type','=','we_not_pay'),('is_amazon_edi_picking','=',True),('po_ack_uploaded','=',True),('state','not in',['cancel','done'])])
            for picking in pickings:
                picking.send_advance_shipment_notice()
    
    @api.model
    def export_inventory_and_cost_from_cron(self,args={}):
        stock_process_obj = self.env['stock.process.wizard']
        vendor_id = args.get('vendor_id')
        if vendor_id:
            stock_process = stock_process_obj.create({'vendor_id' : vendor_id})
            stock_process.prepare_and_send_edi_inventory_message()