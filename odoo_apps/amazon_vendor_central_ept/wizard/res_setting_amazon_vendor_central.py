from odoo import models, fields, api, _
from odoo.exceptions import Warning
from datetime import datetime
from dateutil.relativedelta import relativedelta

class amazon_vendor_central_config(models.TransientModel):
    _name = 'res.config.avc'
    _description = 'res config avc'
       
    name = fields.Char("Vendor Name")
    country_id = fields.Many2one('res.country',string = "Country")
    vendor_qualifier = fields.Char("Vendo Qualifier")
    amazon_qualifier = fields.Char("Amazon Qualifier",default="14")     
    ftp_server_id =fields.Many2one('vendor.ftp.server',string = 'FTP server', )
    is_production_environment = fields.Boolean("Production Environment")
    @api.multi
    def test_amazon_connection(self):
        vendor_exist = self.env['amazon.vendor.instance'].search(['|',('name','=',self.name),('country_id','=',self.country_id.id)])
        if vendor_exist:
            raise Warning('This named Vendor already exist with same configuration...!')
               
        vals = {
            'name':self.name,
            'country_id':self.country_id.id,
            'ftp_server_id':self.ftp_server_id.id,
            'is_production_environment' : self.is_production_environment,
            'vendor_qualifier' : self.vendor_qualifier,
            'amazon_qualifier' : self.amazon_qualifier,
            }
        try:
            vendor = self.env['amazon.vendor.instance'].create(vals)
        except Exception as e :
            raise Warning(str(e))


class amazon_vendor_central_settings(models.TransientModel):
    _inherit='res.config.settings'
    _name="avc.res.config.settings"
    _description ='avc res config settings'
    
    @api.model
    def _get_stock_field_id(self):
        field = self.env['ir.model.fields'].search(
            [('model', '=', 'product.product'),
             ('name', '=', 'virtual_available')],
            limit=1)
        return field
    
    vendor_id = fields.Many2one('amazon.vendor.instance', string='Vendor', ondelete="cascade")
    supplier_id = fields.Char("Supplier ID",help="Supplier ID at Amazon")
    company_id = fields.Many2one('res.company',string='Company')
    country_id = fields.Many2one('res.country',string='Country')
    delivery_type = fields.Selection([('wepay','WePay'),('we_not_pay','We not Pay')], string = 'Delivery Type',help="Delivery Type of Order")
    file_format_for_export = fields.Selection([('flat_file','Flat File'),('edi','EDI')],string = 'File Format for Export',help="File format for export to Vendor central")
    #connection_type = fields.Selection([('test_connection','Test Connection'),('production_connection','Production Connection')], string = 'Connection Type')
    pricelist_id = fields.Many2one('product.pricelist',string="Pricelist")
    order_dispatch_lead_time =  fields.Integer(string = "Order Lead Time", default = 1, help = "The average delay in days between the Routing Request send and ready for order shipment.")
    amazon_edi_carrier_method = fields.Many2one('delivery.carrier',string="Amazon EDI carrier",help="Carrier which is set in Sale Order")
    is_production_environment = fields.Boolean("Production Environment")
    #Purchase Order Import
    #po_import_directory_id = fields.Many2one('ftp.server.directory.list',string="PO Import Directory")
    po_file_import_prefix = fields.Char('PO Import File Prefix')
    warehouse_id = fields.Many2one('stock.warehouse',string="Warehouse",help='Warehouse for Sale Order Import')
    team_id=fields.Many2one('crm.team', 'Sales Team',oldname='section_id')
    fiscal_position_id = fields.Many2one('account.fiscal.position', 'Fiscal Position')
    mismatch_product = fields.Selection([('cancel', 'Cancel'), ('reject', 'Reject'), ('backorder', 'Backorder'), ],
                                        string='If Product not Found')
    
    vendor_code = fields.Char('Vendor code')
    vendor_qualifier = fields.Char("Vendor Qualifier")
    amazon_qualifier = fields.Char("Amazon Qualifier",default="14")     

    so_customer_id = fields.Many2one('res.partner',string="Sale Order Partner")
    #Purchae order ackknowledgement
    #po_export_ack_directory_id = fields.Many2one('ftp.server.directory.list',string="PO Ack Export Directory")
    po_ack_file_export_prefix = fields.Char('PO Ack Export File Prefix')
    auto_confirm_sale_order = fields.Boolean("Auto Confirm Sale Order")
    auto_generate_po_ack = fields.Boolean("Auto Generate PO ACK")
    picking_policy = fields.Selection([('direct', 'Deliver each product when available'),('one', 'Deliver all products at once')],string='Shipping Policy', default='direct',)
    picking_policy_based_on = fields.Selection([('qty_on_hand', 'Quantity On Hand'),
                                                ('forecast_sale', 'Forecast Sale')], default="qty_on_hand",
                                               string="Partially Based On")
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
    #include_forecast_incoming = fields.Boolean(string = "Include Forecast Incoming Quantity", help = "It will allow to send incoming product information in Inventory Report Message")
    production_feed_key = fields.Char(string = 'FEED KEY')
    amazon_unb_id = fields.Char(string = 'Amazon Unb')
    
    #Invoice configuration
    journal_id = fields.Many2one('account.journal','Account Journal',help='Invoice is created in selected Journal')
    invoice_policy = fields.Selection([('order', 'Ordered quantities'),('delivery', 'Delivered quantities'),],string='Invoice Policy')
    #invoice_export_directory_id = fields.Many2one('ftp.server.directory.list',string="Invoice Export Directory")
    invoice_file_export_prefix = fields.Char('Invoice File Prefix')
    
    #advance shipment notice
    #asn_export_directory_id = fields.Many2one('ftp.server.directory.list',string="Shipment Notice Export Directory")
    asn_file_export_prefix = fields.Char('Shipment Notice File Prefix')
    #sales report 
    #sales_report_directory_id = fields.Many2one('ftp.server.directory.list',string="Sales report Export Directory")
    sales_report_file_export_prefix = fields.Char('Sales report File Prefix')
    
    #cron for import purchase order
    auto_import_purchase_order = fields.Boolean(string="Auto Import Purchase Order")
    auto_po_import_next_execution = fields.Datetime('PO Next Execution', help='Next execution time')
    auto_po_import_interval_number = fields.Integer('PO Process Interval Number', help="Repeat every x.")
    auto_po_import_interval_type = fields.Selection([('minutes', 'Minutes'),
            ('hours', 'Hours'), ('work_days', 'Work Days'), ('days', 'Days'), ('weeks', 'Weeks'), ('months', 'Months')], 'PO Process Unit')
    auto_po_import_user_id = fields.Many2one("res.users", string="PO User")
    
    #cron for export Purchase order Acknowledgement
    auto_process_po_ack = fields.Boolean(string='Auto Process Purchase Order?')
    auto_po_process_next_execution = fields.Datetime('PO Ack Next Execution', help='Next execution time')
    auto_po_process_interval_number = fields.Integer('PO Ack Process Interval Number', help="Repeat every x.")
    auto_po_process_interval_type = fields.Selection([('minutes', 'Minutes'),
            ('hours', 'Hours'), ('work_days', 'Work Days'), ('days', 'Days'), ('weeks', 'Weeks'), ('months', 'Months')], 'PO Ack Process Unit')
    auto_po_process_user_id = fields.Many2one("res.users", string="Ack User")
    
    #cron requrement fields for Dispatch Advice
    auto_process_dispatch_advice = fields.Boolean(string = "Auto Process Dispatch Advice?")
    auto_process_dispatch_advice_next_execution = fields.Datetime('Dispatch Advice Next Execution', help='Next execution time')
    auto_process_dispatch_advice_interval_number = fields.Integer('Dispatch Advice Process Interval Number', help="Repeat every x.")
    auto_process_dispatch_advice_interval_type = fields.Selection([('minutes', 'Minutes'),
            ('hours', 'Hours'), ('work_days', 'Work Days'), ('days', 'Days'), ('weeks', 'Weeks'), ('months', 'Months')], 'Dispatch Advice Process Unit')
    auto_process_dispatch_advice_user_id = fields.Many2one("res.users", string="Dispatch Advice User")
    
    #cron requrement fields for Routing request
    auto_process_routing_request = fields.Boolean(string = "Auto Process Routing Request?")
    auto_process_routing_request_next_execution = fields.Datetime('Route Request Next Execution', help='Next execution time')
    auto_process_routing_request_interval_number = fields.Integer('Route Request Process Interval Number', help="Repeat every x.")
    auto_process_routing_request_interval_type = fields.Selection([('minutes', 'Minutes'),
            ('hours', 'Hours'), ('work_days', 'Work Days'), ('days', 'Days'), ('weeks', 'Weeks'), ('months', 'Months')], 'Route Request Process Unit')
    auto_process_routing_request_user_id = fields.Many2one("res.users", string="Route Request User")
    
    #cron requrement fields for Routing Instructions
    auto_process_routing_instruction = fields.Boolean(string = "Auto Process Routing Instruction?")
    auto_process_routing_instruction_next_execution = fields.Datetime('Routing Instructions Next Execution', help='Next execution time')
    auto_process_routing_instruction_interval_number = fields.Integer('Routing Instructions Process Interval Number', help="Repeat every x.")
    auto_process_routing_instruction_interval_type = fields.Selection([('minutes', 'Minutes'),
            ('hours', 'Hours'), ('work_days', 'Work Days'), ('days', 'Days'), ('weeks', 'Weeks'), ('months', 'Months')], 'Routing Instructions Process Unit')
    auto_process_routing_instruction_user_id = fields.Many2one("res.users", string="Routing Instructions User")
    
    #cron requrement fields for export invoice
    auto_process_invoice = fields.Boolean(string = "Auto Export Invoice?")
    auto_process_invoice_next_execution = fields.Datetime('Export Invoice Next Execution', help='Next execution time')
    auto_process_invoice_interval_number = fields.Integer('Export Invoice Process Interval Number', help="Repeat every x.")
    auto_process_invoice_interval_type = fields.Selection([('minutes', 'Minutes'),
            ('hours', 'Hours'), ('work_days', 'Work Days'), ('days', 'Days'), ('weeks', 'Weeks'), ('months', 'Months')], 'Export Invoice Process Unit')
    auto_process_invoice_user_id = fields.Many2one("res.users", string="Invoice User")
    
    #cron requrement fields for export Inventory
    auto_process_inventory = fields.Boolean(string = "Auto Export Inventory?")
    auto_process_inventory_next_execution = fields.Datetime('Export Inventory Next Execution', help='Next execution time')
    auto_process_inventory_interval_number = fields.Integer('Export Inventory Process Interval Number', help="Repeat every x.")
    auto_process_inventory_interval_type = fields.Selection([('minutes', 'Minutes'),
            ('hours', 'Hours'), ('work_days', 'Work Days'), ('days', 'Days'), ('weeks', 'Weeks'), ('months', 'Months')], 'Export Inventory Process Unit')
    auto_process_inventory_user_id = fields.Many2one("res.users", string="Inventory User")

    # cron requrement fields for Import SALES REPORT
    auto_process_sales_report = fields.Boolean(string="Auto Import Sales Report?")
    auto_process_sales_report_next_execution = fields.Datetime('Sales Report Next Execution', help='Next execution time')
    auto_process_sales_report_interval_number = fields.Integer('Sales Report Process Interval Number', help="Repeat every x.")
    auto_process_sales_report_interval_type = fields.Selection([('minutes', 'Minutes'),
                                                             ('hours', 'Hours'), ('work_days', 'Work Days'),
                                                             ('days', 'Days'), ('weeks', 'Weeks'),
                                                             ('months', 'Months')], 'Sales Report Process Unit')
    auto_process_sales_report_user_id = fields.Many2one("res.users", string="Sales Report User")
    
    #For Batch Pickings
    #module_stock_picking_batch = fields.Boolean("Batch Pickings", oldname="module_stock_picking_wave")
    
    #For Product Expiry
    #module_product_expiry = fields.Boolean("Product Expiry")
    
    
    #onchange method of vendor_id
    @api.onchange('vendor_id')
    def onchange_vendor_id(self):
        vendor = self.vendor_id
        if vendor :
            self.supplier_id = vendor.supplier_id or False
            self.company_id = vendor.company_id and vendor.company_id.id or False
            self.country_id = vendor.country_id and vendor.country_id.id or False
            self.delivery_type = vendor.delivery_type or False
            self.file_format_for_export = vendor.file_format_for_export or False
            self.pricelist_id = vendor.pricelist_id and vendor.pricelist_id.id or False
            self.order_dispatch_lead_time = vendor.order_dispatch_lead_time or False
            self.amazon_edi_carrier_method = vendor.amazon_edi_carrier_method or False
            self.vendor_code = vendor.vendor_code or False
            self.vendor_qualifier = vendor.vendor_qualifier or False
            self.amazon_qualifier = vendor.amazon_qualifier or False
            self.so_customer_id = vendor.so_customer_id and vendor.so_customer_id.id or False
            #self.module_stock_picking_batch = vendor.module_stock_picking_batch or False
            #Purchase Order Import
            #self.po_import_directory_id = vendor.po_import_directory_id and vendor.po_import_directory_id.id or False 
            self.po_file_import_prefix = vendor.po_file_import_prefix or False
            self.warehouse_id = vendor.warehouse_id and vendor.warehouse_id.id or False 
            self.team_id = vendor.team_id and vendor.team_id.id or False
            self.fiscal_position_id = vendor.fiscal_position_id and  vendor.fiscal_position_id.id or False 
            self.mismatch_product = vendor.mismatch_product or False
            #Purchae order ackknowledgement
            #self.po_export_ack_directory_id = vendor.po_export_ack_directory_id and vendor.po_export_ack_directory_id.id or False
            self.po_ack_file_export_prefix = vendor.po_ack_file_export_prefix or False
            self.auto_confirm_sale_order = vendor.auto_confirm_sale_order or False 
            self.auto_generate_po_ack = vendor.auto_generate_po_ack or False 
            self.picking_policy = vendor.picking_policy or False 
            self.picking_policy_based_on = vendor.picking_policy_based_on or False 
            #Routing Request
            #self.route_request_export_directory_id = vendor.route_request_export_directory_id and vendor.route_request_export_directory_id.id or False
            self.route_request_file_export_prefix = vendor.route_request_file_export_prefix or False 
            #Routing Information
            #self.route_info_export_directory_id = vendor.route_info_export_directory_id and vendor.route_info_export_directory_id.id or False 
            self.route_info_file_import_prefix = vendor.route_info_file_import_prefix or False 
            #Inventory and cost
            self.amazon_gln_number = vendor.amazon_gln_number or False 
            #self.is_allow_stock_export_from_multi_warehouse = vendor.is_allow_stock_export_from_multi_warehouse or False 
            self.warehouse_ids = vendor.warehouse_ids and [(6,0,vendor.warehouse_ids.ids)] or False
            self.product_stock_field_id = vendor.product_stock_field_id and vendor.product_stock_field_id.id or False 
            #self.inventory_export_directory_id = vendor.inventory_export_directory_id or vendor.inventory_export_directory_id.id or False
            self.inventory_file_export_prefix = vendor.inventory_file_export_prefix or False 
            #self.include_forecast_incoming = vendor.include_forecast_incoming or False 
            self.production_feed_key = vendor.production_feed_key or False  
            self.amazon_unb_id = vendor.amazon_unb_id or False
            #Invoice configuration
            self.journal_id = vendor.journal_id and vendor.journal_id.id or False 
            self.invoice_policy = vendor.invoice_policy or False
            #self.invoice_export_directory_id = vendor.invoice_export_directory_id and vendor.invoice_export_directory_id.id or False
            self.invoice_file_export_prefix = vendor.invoice_file_export_prefix  
            #advance shipment notice
            #self.asn_export_directory_id = vendor.asn_export_directory_id and vendor.asn_export_directory_id.id or False 
            self.asn_file_export_prefix = vendor.asn_file_export_prefix or False 
            #sales report 
            #self.sales_report_directory_id = vendor.sales_report_directory_id and vendor.sales_report_directory_id.id or False
            self.sales_report_file_export_prefix = vendor.sales_report_file_export_prefix or False
            self.test_ftp_connection = vendor.test_ftp_connection and vendor.test_ftp_connection.id or False 
            self.test_po_directory_id = vendor.test_po_directory_id and vendor.test_po_directory_id.id or False 
            self.test_po_ack_directory_id = vendor.test_po_ack_directory_id and vendor.test_po_ack_directory_id.id or False
            self.test_route_req_directory_id = vendor.test_route_req_directory_id and vendor.test_route_req_directory_id.id or False
            self.test_route_info_drectory_id = vendor.test_route_info_drectory_id and vendor.test_route_info_drectory_id.id or False 
            self.test_inv_cost_directory_id = vendor.test_inv_cost_directory_id and vendor.test_inv_cost_directory_id.id or False 
            self.test_invoice_directory_id = vendor.test_invoice_directory_id and vendor.test_invoice_directory_id.id or False 
            self.test_asn_directory_id = vendor.test_asn_directory_id and vendor.test_asn_directory_id.id or False
            self.test_sale_report_directory_id = vendor.test_sale_report_directory_id and vendor.test_sale_report_directory_id.id or False 
    
            self.production_ftp_connection = vendor.production_ftp_connection and vendor.production_ftp_connection.id or False 
            self.production_po_directory_id = vendor.production_po_directory_id and vendor.production_po_directory_id.id or False
            self.production_po_ack_directory_id = vendor.production_po_ack_directory_id and vendor.production_po_ack_directory_id.id or False 
            self.production_route_req_directory_id = vendor.production_route_req_directory_id and vendor.production_route_req_directory_id.id or False
            self.production_route_info_drectory_id = vendor.production_route_info_drectory_id and vendor.production_route_info_drectory_id.id or False   
            self.production_inv_cost_directory_id = vendor.production_inv_cost_directory_id and vendor.production_inv_cost_directory_id.id or False
            self.production_invoice_directory_id = vendor.production_invoice_directory_id and vendor.production_invoice_directory_id.id or False 
            self.production_asn_directory_id = vendor.production_asn_directory_id and vendor.production_asn_directory_id.id or False
            self.production_sale_report_directory_id = vendor.production_sale_report_directory_id and vendor.production_sale_report_directory_id.id or False

            try:
                po_order_import_cron = vendor and self.env.ref('amazon_vendor_central_ept.ir_cron_avc_edi_auto_import_po_%d' % (vendor.id), raise_if_not_found=False)
            except:
                po_order_import_cron = False
            if po_order_import_cron:
                self.auto_po_import_interval_number = po_order_import_cron.interval_number or False
                self.auto_po_import_interval_type = po_order_import_cron.interval_type or False
                self.auto_po_import_next_execution = po_order_import_cron.nextcall or False
                self.auto_po_import_user_id = po_order_import_cron.user_id.id or False
                
            try:
                po_ack_export_cron = vendor and self.env.ref('amazon_vendor_central_ept.ir_cron_avc_edi_auto_export_po_ack_%d' % (vendor.id), raise_if_not_found=False)
            except:
                po_ack_export_cron = False
            if po_ack_export_cron:
                self.auto_po_process_interval_number = po_ack_export_cron.interval_number or False
                self.auto_po_process_interval_type = po_ack_export_cron.interval_type or False
                self.auto_po_process_next_execution = po_ack_export_cron.nextcall or False
                self.auto_po_process_user_id = po_ack_export_cron.user_id.id or False
                
            try:
                route_request_cron = vendor and self.env.ref('amazon_vendor_central_ept.ir_cron_avc_edi_import_route_request_%d' % (vendor.id), raise_if_not_found=False)
            except:
                route_request_cron = False
            if route_request_cron:
                self.auto_process_routing_request_interval_number = route_request_cron.interval_number or False
                self.auto_process_routing_request_interval_type = route_request_cron.interval_type or False
                self.auto_process_routing_request_next_execution = route_request_cron.nextcall or False
                self.auto_process_routing_request_user_id = route_request_cron.user_id.id or False
                
            try:
                route_info_cron = vendor and self.env.ref('amazon_vendor_central_ept.ir_cron_avc_edi_auto_process_routing_instruction_%d' % (vendor.id), raise_if_not_found=False)
            except:
                route_info_cron = False
            if route_info_cron:
                self.auto_process_routing_instruction_interval_number = route_info_cron.interval_number or False
                self.auto_process_routing_instruction_interval_type = route_info_cron.interval_type or False
                self.auto_process_routing_instruction_next_execution = route_info_cron.nextcall or False
                self.auto_process_routing_instruction_user_id = route_info_cron.user_id.id or False
                
            try:
                advance_shipment_notice_cron = vendor and self.env.ref('amazon_vendor_central_ept.ir_cron_avc_edi_auto_process_dispatch_advice_%d' % (vendor.id), raise_if_not_found=False)
            except:
                advance_shipment_notice_cron = False
            if po_ack_export_cron:
                self.auto_process_dispatch_advice_interval_number = advance_shipment_notice_cron.interval_number or False
                self.auto_process_dispatch_advice_interval_type = advance_shipment_notice_cron.interval_type or False
                self.auto_process_dispatch_advice_next_execution = advance_shipment_notice_cron.nextcall or False
                self.auto_process_dispatch_advice_user_id = advance_shipment_notice_cron.user_id.id or False
            
            
            try:
                inventory_cron = vendor and self.env.ref('amazon_vendor_central_ept.ir_cron_inventory_and_cost_export_%d' % (vendor.id), raise_if_not_found=False)
            except:
                advance_shipment_notice_cron = False
            if po_ack_export_cron:
                self.auto_process_inventory_interval_number = inventory_cron.interval_number or False
                self.auto_process_inventory_interval_type = inventory_cron.interval_type or False
                self.auto_process_inventory_next_execution = inventory_cron.nextcall or False
                self.auto_process_inventory_user_id = inventory_cron.user_id.id or False
    
    
    #super class execute method.
    @api.multi
    def execute(self):
        vendor = self.vendor_id
        values = {}
        ctx = {}
        res = super(amazon_vendor_central_settings, self).execute()
        if vendor:
            values['supplier_id'] = self.supplier_id or False
            values['company_id'] = self.company_id and self.company_id.id or False  
            values['country_id'] = self.country_id and self.country_id.id or False 
            values['delivery_type'] = self.delivery_type or False
            values['file_format_for_export'] = self.file_format_for_export or False
#             values['ftp_server_id'] = self.ftp_server_id and self.ftp_server_id.id or False 
#             values['connection_type'] = self.connection_type or False
            values['so_customer_id'] = self.so_customer_id and self.so_customer_id.id or False
            values['vendor_code'] = self.vendor_code or False
            values['vendor_qualifier'] = self.vendor_qualifier or False
            values['amazon_qualifier'] = self.amazon_qualifier or False
            values['pricelist_id'] = self.pricelist_id and self.pricelist_id.id or False
            values['order_dispatch_lead_time'] = self.order_dispatch_lead_time or False
            values['amazon_edi_carrier_method'] = self.amazon_edi_carrier_method and self.amazon_edi_carrier_method.id or False         
            #Purchase Order Import
            #values['po_import_directory_id'] = self.po_import_directory_id and self.po_import_directory_id.id or False 
            values['po_file_import_prefix'] = self.po_file_import_prefix or False 
            values['warehouse_id'] = self.warehouse_id and self.warehouse_id.id or False 
            values['team_id'] = self.team_id and self.team_id.id or False
            values['fiscal_position_id'] = self.fiscal_position_id and self.fiscal_position_id.id or False
            #Purchae order ackknowledgement
            #values['po_export_ack_directory_id'] = self.po_export_ack_directory_id and self.po_export_ack_directory_id.id or False
            values['po_ack_file_export_prefix'] = self.po_ack_file_export_prefix or False
            values['auto_confirm_sale_order'] = self.auto_confirm_sale_order or False
            values['auto_generate_po_ack'] = self.auto_generate_po_ack or False 
            values['picking_policy'] = self.picking_policy or False
            values['mismatch_product'] = self.mismatch_product or False
            #Routing Request
            #values['route_request_export_directory_id'] = self.route_request_export_directory_id and self.route_request_export_directory_id.id or False
            values['route_request_file_export_prefix'] = self.route_request_file_export_prefix or False
    
            #Routing Information
            #values['route_info_export_directory_id'] = self.route_info_export_directory_id and self.route_info_export_directory_id.id or False 
            values['route_info_file_import_prefix'] = self.route_info_file_import_prefix or False 
    
            #Inventory and cost
            values['amazon_gln_number'] = self.amazon_gln_number or False
            #values['is_allow_stock_export_from_multi_warehouse'] = self.is_allow_stock_export_from_multi_warehouse or False  
            values['warehouse_ids'] = self.warehouse_ids and [(6,0,self.warehouse_ids.ids)] or False
            values['product_stock_field_id'] = self.product_stock_field_id and self.product_stock_field_id.id or False
            #values['module_stock_picking_batch'] = self.module_stock_picking_batch or False
            #values['inventory_export_directory_id'] = self.inventory_export_directory_id and self.inventory_export_directory_id.id or False
            values['inventory_file_export_prefix'] = self.inventory_file_export_prefix or False 
            #values['include_forecast_incoming'] = self.include_forecast_incoming or False 
            values['production_feed_key'] = self.production_feed_key or False
            values['amazon_unb_id'] = self.amazon_unb_id or False 
            
            #General Configuration
            #values['module_product_expiry'] = self.module_product_expiry or False           
            
            #Invoice configuration
            values['journal_id'] = self.journal_id and self.journal_id.id or False
            values['invoice_policy'] = self.invoice_policy or False 
            #values['invoice_export_directory_id'] = self.invoice_export_directory_id and self.invoice_export_directory_id.id or False
            values['invoice_file_export_prefix'] = self.invoice_file_export_prefix or False 
    
            #advance shipment notice
            #values['asn_export_directory_id'] = self.asn_export_directory_id and self.asn_export_directory_id.id or False 
            values['asn_file_export_prefix'] = self.asn_file_export_prefix or False 
            #sales report 
            #values['sales_report_directory_id'] = self.sales_report_directory_id and self.sales_report_directory_id.id or False
            values['sales_report_file_export_prefix'] = self.sales_report_file_export_prefix or False 
            
            vendor.write(values)
            self.setup_amazon_edi_import_po_import_cron(vendor)
            self.setup_amazon_edi_export_po_ack(vendor)
            self.setup_amazon_edi_import_route_request(vendor)
            self.setup_amazon_edi_import_route_info(vendor)
            self.setup_amazon_edi_export_advance_shipment_notice(vendor)
            self.setup_amazon_edi_import_inventory_request(vendor)
        return res
            
    @api.multi
    def setup_amazon_edi_import_po_import_cron(self, vendor):
        """
        It will create cron if not exist and if exist it will active and deactive according to user's choice.
        @param instance: Recordset of Instance.
        @return : True
        """
        if self.auto_import_purchase_order:
            try:
                cron_exist = self.env.ref('amazon_vendor_central_ept.ir_cron_avc_edi_auto_import_po_%d' % (vendor.id), raise_if_not_found=False)
            except:
                cron_exist = False
#             nextcall = datetime.now()
#             nextcall += _intervalTypes[self.order_import_interval_type](self.order_import_interval_number)
#'code':"model.auto_export_tracking_information({'instance_id':%d})" % (instance.id),
            vals = {
                    'active' : True,
                    'interval_number':self.auto_po_import_interval_number,
                    'interval_type':self.auto_po_import_interval_type,
                    'nextcall':self.auto_po_import_next_execution,
                    'code':"model.sync_amazon_po_from_cron({'vendor_id':%d})" % (vendor.id),
                    'user_id': self.auto_po_import_user_id and self.auto_po_import_user_id.id}

            if cron_exist:
                #vals.update({'name' : cron_exist.name})
                cron_exist.write(vals)
            else:
                try:
                    import_order_cron = self.env.ref('amazon_vendor_central_ept.ir_cron_avc_edi_auto_import_po')
                except:
                    import_order_cron = False
                if not import_order_cron:
                    raise Warning('Core settings of Vendor Central are deleted, please upgrade Amazon Vendor Central module to back this settings.')

                name = vendor.name + ' : ' + import_order_cron.name
                vals.update({'name' : name})
                new_cron = import_order_cron.copy(default=vals)
                self.env['ir.model.data'].create({'module':'amazon_vendor_central_ept',
                                                  'name':'amazon_vendor_central_ept.ir_cron_avc_edi_auto_import_po_%d' % (vendor.id),
                                                  'model': 'ir.cron',
                                                  'res_id' : new_cron.id,
                                                  'noupdate' : True
                                                  })
        else:
            try:
                cron_exist = self.env.ref('amazon_vendor_central_ept.ir_cron_avc_edi_auto_import_po_%d' % (vendor.id))
            except:
                cron_exist = False

            if cron_exist:
                cron_exist.write({'active':False})
        return True
    
    @api.multi
    def setup_amazon_edi_export_po_ack(self, vendor):
        """
        It will create cron if not exist and if exist it will active and deactive according to user's choice.
        @param instance: Recordset of Instance.
        @return : True
        """
        if self.auto_process_po_ack:
            try:
                cron_exist = self.env.ref('amazon_vendor_central_ept.ir_cron_avc_edi_auto_export_po_ack_%d' % (vendor.id), raise_if_not_found=False)
            except:
                cron_exist = False
#             nextcall = datetime.now()
#             nextcall += _intervalTypes[self.order_import_interval_type](self.order_import_interval_number)
            vals = {
                    'active' : True,
                    'interval_number':self.auto_po_process_interval_number,
                    'interval_type':self.auto_po_process_interval_type,
                    'nextcall':self.auto_po_process_next_execution,
                    'code':"model.export_po_ack_from_cron({'vendor_id':%d})" % (vendor.id),
                    'user_id': self.auto_po_process_user_id and self.auto_po_process_user_id.id}

            if cron_exist:
                #vals.update({'name' : cron_exist.name})
                cron_exist.write(vals)
            else:
                try:
                    po_ack_cron = self.env.ref('amazon_vendor_central_ept.ir_cron_avc_edi_auto_export_po_ack')
                except:
                    po_ack_cron = False
                if not po_ack_cron:
                    raise Warning('Core settings of Vendor Central are deleted, please upgrade Amazon Vendor Central module to back this settings.')

                name = vendor.name + ' : ' + po_ack_cron.name
                vals.update({'name' : name})
                new_cron = po_ack_cron.copy(default=vals)
                self.env['ir.model.data'].create({'module':'amazon_vendor_central_ept',
                                                  'name':'amazon_vendor_central_ept.ir_cron_avc_edi_auto_export_po_ack_%d' % (vendor.id),
                                                  'model': 'ir.cron',
                                                  'res_id' : new_cron.id,
                                                  'noupdate' : True
                                                  })
        else:
            try:
                cron_exist = self.env.ref('amazon_vendor_central_ept.ir_cron_avc_edi_auto_export_po_ack_%d' % (vendor.id))
            except:
                cron_exist = False

            if cron_exist:
                cron_exist.write({'active':False})
        return True
    
    
    @api.multi
    def setup_amazon_edi_import_inventory_request(self, vendor):
        """
        It will create cron if not exist and if exist it will active and deactive according to user's choice.
        @param instance: Recordset of Instance.
        @return : True
        """
        if self.auto_process_inventory:
            try:
                cron_exist = self.env.ref('amazon_vendor_central_ept.ir_cron_inventory_and_cost_export_%d' % (vendor.id), raise_if_not_found=False)
            except:
                cron_exist = False
#             nextcall = datetime.now()
#             nextcall += _intervalTypes[self.order_import_interval_type](self.order_import_interval_number)
            vals = {
                    'active' : True,
                    'interval_number':self.auto_process_inventory_interval_number,
                    'interval_type':self.auto_process_inventory_interval_type,
                    'nextcall':self.auto_process_inventory_next_execution,
                    'code':"model.export_inventory_and_cost_from_cron({'vendor_id':%d})" % (vendor.id),
                    'user_id': self.auto_process_inventory_user_id and self.auto_process_inventory_user_id.id}

            if cron_exist:
                #vals.update({'name' : cron_exist.name})
                cron_exist.write(vals)
            else:
                try:
                    routin_request_cron = self.env.ref('amazon_vendor_central_ept.ir_cron_inventory_and_cost_export')
                except:
                    routin_request_cron = False
                if not routin_request_cron:
                    raise Warning('Core settings of Vendor Central are deleted, please upgrade Amazon Vendor Central module to back this settings.')

                name = vendor.name + ' : ' + routin_request_cron.name
                vals.update({'name' : name})
                new_cron = routin_request_cron.copy(default=vals)
                self.env['ir.model.data'].create({'module':'amazon_vendor_central_ept',
                                                  'name':'amazon_vendor_central_ept.ir_cron_inventory_and_cost_export_%d' % (vendor.id),
                                                  'model': 'ir.cron',
                                                  'res_id' : new_cron.id,
                                                  'noupdate' : True
                                                  })
        else:
            try:
                cron_exist = self.env.ref('amazon_vendor_central_ept.ir_cron_avc_edi_import_route_request_%d' % (vendor.id))
            except:
                cron_exist = False

            if cron_exist:
                cron_exist.write({'active':False})
        return True

    
    
    @api.multi
    def setup_amazon_edi_import_route_request(self, vendor):
        """
        It will create cron if not exist and if exist it will active and deactive according to user's choice.
        @param instance: Recordset of Instance.
        @return : True
        """
        if self.auto_process_routing_request:
            try:
                cron_exist = self.env.ref('amazon_vendor_central_ept.ir_cron_avc_edi_import_route_request_%d' % (vendor.id), raise_if_not_found=False)
            except:
                cron_exist = False
#             nextcall = datetime.now()
#             nextcall += _intervalTypes[self.order_import_interval_type](self.order_import_interval_number)
            vals = {
                    'active' : True,
                    'interval_number':self.auto_process_routing_request_interval_number,
                    'interval_type':self.auto_process_routing_request_interval_type,
                    'nextcall':self.auto_process_routing_request_next_execution,
                    'code':"model.export_route_request_from_cron({'vendor_id':%d})" % (vendor.id),
                    'user_id': self.auto_process_routing_request_user_id and self.auto_process_routing_request_user_id.id}

            if cron_exist:
                #vals.update({'name' : cron_exist.name})
                cron_exist.write(vals)
            else:
                try:
                    routin_request_cron = self.env.ref('amazon_vendor_central_ept.ir_cron_avc_edi_import_route_request')
                except:
                    routin_request_cron = False
                if not routin_request_cron:
                    raise Warning('Core settings of Vendor Central are deleted, please upgrade Amazon Vendor Central module to back this settings.')

                name = vendor.name + ' : ' + routin_request_cron.name
                vals.update({'name' : name})
                new_cron = routin_request_cron.copy(default=vals)
                self.env['ir.model.data'].create({'module':'amazon_vendor_central_ept',
                                                  'name':'amazon_vendor_central_ept.ir_cron_avc_edi_import_route_request_%d' % (vendor.id),
                                                  'model': 'ir.cron',
                                                  'res_id' : new_cron.id,
                                                  'noupdate' : True
                                                  })
        else:
            try:
                cron_exist = self.env.ref('amazon_vendor_central_ept.ir_cron_avc_edi_import_route_request_%d' % (vendor.id))
            except:
                cron_exist = False

            if cron_exist:
                cron_exist.write({'active':False})
        return True
    
    @api.multi
    def setup_amazon_edi_import_route_info(self, vendor):
        """
        It will create cron if not exist and if exist it will active and deactive according to user's choice.
        @param instance: Recordset of Instance.
        @return : True
        """
        if self.auto_process_routing_instruction:
            try:
                cron_exist = self.env.ref('amazon_vendor_central_ept.ir_cron_avc_edi_auto_process_routing_instruction_%d' % (vendor.id), raise_if_not_found=False)
            except:
                cron_exist = False
#             nextcall = datetime.now()
#             nextcall += _intervalTypes[self.order_import_interval_type](self.order_import_interval_number)
            vals = {
                    'active' : True,
                    'interval_number':self.auto_process_routing_instruction_interval_number,
                    'interval_type':self.auto_process_routing_instruction_interval_type,
                    'nextcall':self.auto_process_routing_instruction_next_execution,
                    'code':"model.import_route_info_form_cron({'vendor_id':%d})" % (vendor.id),
                    'user_id': self.auto_process_routing_instruction_user_id and self.auto_process_routing_instruction_user_id.id}

            if cron_exist:
                #vals.update({'name' : cron_exist.name})
                cron_exist.write(vals)
            else:
                try:
                    route_info_cron = self.env.ref('amazon_vendor_central_ept.ir_cron_avc_edi_auto_process_routing_instruction')
                except:
                    route_info_cron = False
                if not route_info_cron:
                    raise Warning('Core settings of Vendor Central are deleted, please upgrade Amazon Vendor Central module to back this settings.')

                name = vendor.name + ' : ' + route_info_cron.name
                vals.update({'name' : name})
                new_cron = route_info_cron.copy(default=vals)
                self.env['ir.model.data'].create({'module':'amazon_vendor_central_ept',
                                                  'name':'amazon_vendor_central_ept.ir_cron_avc_edi_auto_process_routing_instruction_%d' % (vendor.id),
                                                  'model': 'ir.cron',
                                                  'res_id' : new_cron.id,
                                                  'noupdate' : True
                                                  })
        else:
            try:
                cron_exist = self.env.ref('amazon_vendor_central_ept.ir_cron_avc_edi_auto_process_routing_instruction_%d' % (vendor.id))
            except:
                cron_exist = False

            if cron_exist:
                cron_exist.write({'active':False})
        return True
    
    @api.multi
    def setup_amazon_edi_export_advance_shipment_notice(self, vendor):
        """
        It will create cron if not exist and if exist it will active and deactive according to user's choice.
        @param instance: Recordset of Instance.
        @return : True
        """
        if self.auto_process_dispatch_advice:
            try:
                cron_exist = self.env.ref('amazon_vendor_central_ept.ir_cron_avc_edi_auto_process_dispatch_advice_%d' % (vendor.id), raise_if_not_found=False)
            except:
                cron_exist = False
#             nextcall = datetime.now()
#             nextcall += _intervalTypes[self.order_import_interval_type](self.order_import_interval_number)
            vals = {
                    'active' : True,
                    'interval_number':self.auto_process_dispatch_advice_interval_number,
                    'interval_type':self.auto_process_dispatch_advice_interval_type,
                    'nextcall':self.auto_process_dispatch_advice_next_execution,
                    'code':"model.export_advance_shipment_notice_from_cron({'vendor_id':%d})" % (vendor.id),
                    'user_id': self.auto_process_dispatch_advice_user_id and self.auto_process_dispatch_advice_user_id.id}

            if cron_exist:
                #vals.update({'name' : cron_exist.name})
                cron_exist.write(vals)
            else:
                try:
                    shipment_notice_cron = self.env.ref('amazon_vendor_central_ept.ir_cron_avc_edi_auto_process_dispatch_advice')
                except:
                    shipment_notice_cron = False
                if not shipment_notice_cron:
                    raise Warning('Core settings of Vendor Central are deleted, please upgrade Amazon Vendor Central module to back this settings.')

                name = vendor.name + ' : ' + shipment_notice_cron.name
                vals.update({'name' : name})
                new_cron = shipment_notice_cron.copy(default=vals)
                self.env['ir.model.data'].create({'module':'amazon_vendor_central_ept',
                                                  'name':'amazon_vendor_central_ept.ir_cron_avc_edi_auto_process_dispatch_advice_%d' % (vendor.id),
                                                  'model': 'ir.cron',
                                                  'res_id' : new_cron.id,
                                                  'noupdate' : True
                                                  })
        else:
            try:
                cron_exist = self.env.ref('amazon_vendor_central_ept.ir_cron_avc_edi_auto_process_dispatch_advice_%d' % (vendor.id))
            except:
                cron_exist = False

            if cron_exist:
                cron_exist.write({'active':False})
        return True