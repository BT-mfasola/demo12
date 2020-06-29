from odoo import models,fields,api,_

class res_config_ftp_server(models.TransientModel):
    _inherit = 'res.config.settings'
    _name = 'ftp.server.config.setting'
    _description = 'res config settings'
    
    vendor_id = fields.Many2one('amazon.vendor.instance',string="Vendor")
    test_ftp_connection = fields.Many2one('vendor.ftp.server',string="Test FTP server")
    test_po_directory_id = fields.Many2one('ftp.server.directory.list',string="Test PO Import")
    test_po_ack_directory_id = fields.Many2one('ftp.server.directory.list',string="Test PO ACK ")
    test_route_req_directory_id = fields.Many2one('ftp.server.directory.list',string="PO Route request ")
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
        
    @api.onchange('vendor_id')
    def onchange_vendor_id(self):
        vendor = self.vendor_id
        if vendor :
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
    
    @api.onchange('test_ftp_connection')
    def onchange_test_ftp(self):
        test_ftp = self.test_ftp_connection
        if not test_ftp:
            self.test_po_directory_id = False
            self.test_po_ack_directory_id = False
            self.test_route_req_directory_id = False
            self.test_route_info_drectory_id = False
            self.test_inv_cost_directory_id = False
            self.test_invoice_directory_id = False
            self.test_asn_directory_id = False
            self.test_sale_report_directory_id = False
        if test_ftp:
            vendor = self.vendor_id 
            self.test_po_directory_id = vendor.test_po_directory_id and vendor.test_po_directory_id.id or False 
            self.test_po_ack_directory_id = vendor.test_po_ack_directory_id and vendor.test_po_ack_directory_id.id or False
            self.test_route_req_directory_id = vendor.test_route_req_directory_id and vendor.test_route_req_directory_id.id or False
            self.test_route_info_drectory_id = vendor.test_route_info_drectory_id and vendor.test_route_info_drectory_id.id or False 
            self.test_inv_cost_directory_id = vendor.test_inv_cost_directory_id and vendor.test_inv_cost_directory_id.id or False 
            self.test_invoice_directory_id = vendor.test_invoice_directory_id and vendor.test_invoice_directory_id.id or False 
            self.test_asn_directory_id = vendor.test_asn_directory_id and vendor.test_asn_directory_id.id or False
            self.test_sale_report_directory_id = vendor.test_sale_report_directory_id and vendor.test_sale_report_directory_id.id or False
    
    @api.onchange('production_ftp_connection')
    def onchange_production_ftp(self):
        production_ftp = self.production_ftp_connection
        if not production_ftp:
            self.production_po_directory_id = False
            self.production_po_ack_directory_id = False
            self.production_route_req_directory_id = False
            self.production_route_info_drectory_id = False
            self.production_inv_cost_directory_id = False
            self.production_invoice_directory_id = False
            self.production_asn_directory_id = False
            self.production_sale_report_directory_id = False
        if production_ftp:
            vendor = self.vendor_id 
            self.production_po_directory_id = vendor.production_po_directory_id and vendor.production_po_directory_id.id or False
            self.production_po_ack_directory_id = vendor.production_po_ack_directory_id and vendor.production_po_ack_directory_id.id or False 
            self.production_route_req_directory_id = vendor.production_route_req_directory_id and vendor.production_route_req_directory_id.id or False
            self.production_route_info_drectory_id = vendor.production_route_info_drectory_id and vendor.production_route_info_drectory_id.id or False   
            self.production_inv_cost_directory_id = vendor.production_inv_cost_directory_id and vendor.production_inv_cost_directory_id.id or False
            self.production_invoice_directory_id = vendor.production_invoice_directory_id and vendor.production_invoice_directory_id.id or False 
            self.production_asn_directory_id = vendor.production_asn_directory_id and vendor.production_asn_directory_id.id or False
            self.production_sale_report_directory_id = vendor.production_sale_report_directory_id and vendor.production_sale_report_directory_id.id or False
    
    
    @api.multi
    def execute(self):
        vendor = self.vendor_id
        values = {}
        ctx = {}
        res = super(res_config_ftp_server, self).execute()
        if vendor :
            values['test_ftp_connection'] = self.test_ftp_connection and self.test_ftp_connection.id or False 
            values['test_po_directory_id'] = self.test_po_directory_id and self.test_po_directory_id.id or False 
            values['test_po_ack_directory_id'] = self.test_po_ack_directory_id and self.test_po_ack_directory_id.id or False
            values['test_route_req_directory_id'] = self.test_route_req_directory_id and self.test_route_req_directory_id.id or False 
            values['test_route_info_drectory_id'] = self.test_route_info_drectory_id and self.test_route_info_drectory_id.id or False 
            values['test_inv_cost_directory_id'] = self.test_inv_cost_directory_id and self.test_inv_cost_directory_id.id or False 
            values['test_invoice_directory_id'] = self.test_invoice_directory_id and self.test_invoice_directory_id.id or False 
            values['test_asn_directory_id'] = self.test_asn_directory_id and self.test_asn_directory_id.id or False
            values['test_sale_report_directory_id'] = self.test_sale_report_directory_id and self.test_sale_report_directory_id.id or False
             
    
            values['production_ftp_connection'] = self.production_ftp_connection and self.production_ftp_connection.id or False
            values['production_po_directory_id'] = self.production_po_directory_id and self.production_po_directory_id.id or False
            values['production_po_ack_directory_id'] = self.production_po_ack_directory_id and self.production_po_ack_directory_id.id or False 
            values['production_route_req_directory_id'] = self.production_route_req_directory_id and self.production_route_req_directory_id.id or False
            values['production_route_info_drectory_id'] = self.production_route_info_drectory_id and self.production_route_info_drectory_id.id or False
            values['production_inv_cost_directory_id'] = self.production_inv_cost_directory_id and self.production_inv_cost_directory_id.id or False
            values['production_invoice_directory_id'] = self.production_invoice_directory_id and self.production_invoice_directory_id.id or False 
            values['production_asn_directory_id'] = self.production_asn_directory_id and self.production_asn_directory_id.id or False
            values['production_sale_report_directory_id'] = self.production_sale_report_directory_id and self.production_sale_report_directory_id.id or False
            
            vendor.write(values)
        return res
            