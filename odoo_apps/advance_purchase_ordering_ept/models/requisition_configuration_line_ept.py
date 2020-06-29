from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError

class RequisitionConfigurationLine(models.Model):
    _name = 'requisition.configuration.line.ept'
    _description = "Reorder Planning"


    @api.model
    def _get_default_backup_stock_days(self):
        return self.env['ir.config_parameter'].sudo().get_param('inventory_coverage_report_ept.is_default_requisition_backup_stock_days')
        
        
    requisition_backup_stock_days = fields.Integer(string='Keep Stock of X Days', default=_get_default_backup_stock_days)
    requisition_estimated_delivery_time = fields.Integer(string='Estimated Delivery Time')    
        
    warehouse_id = fields.Many2one('stock.warehouse', string='Requested Warehouse', index=True)
    destination_warehouse_id = fields.Many2one('stock.warehouse', string='Delivery Warehouse', index=True)
    purchase_currency_id = fields.Many2one('res.currency', string="Purchase Currency")
    purchase_order_id = fields.Many2one('purchase.order', string="Purchase Order")
    requisition_process_id = fields.Many2one('requisition.process.ept', string='Reorder Process', index=True)
    
    
     
    @api.multi
    @api.constrains('warehouse_id', 'requisition_process_id')
    def _check_uniq_warehouse_id(self):
        for record in self :
            config_line_exists = self.search([('id', '!=', record.id), ('requisition_process_id', '=', record.requisition_process_id.id), ('warehouse_id', '=', record.warehouse_id.id)])
            if config_line_exists :
                raise ValidationError(_('Requested Warehouse must be unique per line'))
    
    
    
    @api.multi
    @api.constrains('requisition_backup_stock_days', 'requisition_estimated_delivery_time')
    def check_security_days(self):
        for record in self:
            if record.requisition_backup_stock_days < 0:
                raise ValidationError(_("Stock Days can not be less than 0"))
            
            if record.requisition_estimated_delivery_time < 0:
                raise ValidationError(_("Estimated Delivery Time can not be less than 0"))
        return True
    
    
    
        
    @api.multi
    @api.onchange('destination_warehouse_id')
    def onchange_destination_warehouse_id(self):
        for record in self :
            dest_warehouse = record.destination_warehouse_id
            if not dest_warehouse :
                continue
            requisition_process = record.requisition_process_id
            if not requisition_process :
                continue
            partner = requisition_process.partner_id
            if not partner :
                continue
            partner = partner.with_context(force_company=dest_warehouse.company_id.id)
            currency = partner.property_purchase_currency_id
            if not currency :
                currency = dest_warehouse and dest_warehouse.company_id and dest_warehouse.company_id.currency_id or False
            record.purchase_currency_id = currency
        return 
    
    
    @api.multi
    def get_warehouse_for_purchase_order(self):
        self.ensure_one()
        warehouse = self.destination_warehouse_id
        return warehouse
