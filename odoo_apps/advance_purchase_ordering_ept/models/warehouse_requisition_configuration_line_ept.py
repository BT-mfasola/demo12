from odoo import fields, models, api, _
from odoo.exceptions import  ValidationError, UserError

class WarehouseRequisitionProcessLine(models.Model):
    _name = 'warehouse.requisition.configuration.line.ept'
    _description = "Procurement Process Warehouse Planning"

    
    requisition_estimated_delivery_time = fields.Integer(string='Estimated Delivery Time')
    requisition_backup_stock_days = fields.Integer(string='Keep Stock of X Days', default=lambda self: self.env['ir.config_parameter'].sudo().get_param('inventory_coverage_report_ept.is_default_requisition_backup_stock_days') or 1)
   
    warehouse_id = fields.Many2one('stock.warehouse', string='Requested Warehouse', index=True)
    warehouse_requisition_process_id = fields.Many2one('warehouse.requisition.process.ept', string='Procurement Process', index=True, copy=False)
    destination_warehouse_id = fields.Many2one('stock.warehouse', string='Delivery warehouse', index=True)
    intercompany_transfer_id = fields.Many2one('inter.company.transfer.ept', string="Inter-Company Transfer")
     
    @api.multi
    @api.constrains('warehouse_id', 'warehouse_requisition_process_id')
    def _check_uniq_warehouse_id(self):
        for line in self :
            config_line_exists = self.search([('id', '!=', line.id), ('warehouse_requisition_process_id', '=', line.warehouse_requisition_process_id.id), ('warehouse_id', '=', line.warehouse_id.id)])
            if config_line_exists :
                raise ValidationError(_('Requested Warehouse must be unique per line'))
     
     
    @api.multi
    @api.constrains('destination_warehouse_id')
    def _check_dest_warehouse(self):
        for line in self:
            if line.warehouse_requisition_process_id.source_warehouse_id == line.warehouse_id:
                if line.warehouse_id != line.destination_warehouse_id:
                    raise ValidationError(_('Delivery Warehouse Must be Same as Source Warehouse If Warehouse in Configuration Line and Source Warehouse Both are Same.'))
    
    @api.multi
    @api.constrains('requisition_backup_stock_days', 'requisition_estimated_delivery_time')
    def check_security_days(self):
        for obj in self:
            if obj.requisition_backup_stock_days < 0:
                raise ValidationError(_("Stock Days can not be less than 0"))
            
            if obj.requisition_estimated_delivery_time < 0:
                raise ValidationError(_("Estimated Delivery Time can not be less than 0"))
        return True        
    
    @api.multi
    def is_create_intercompany_transfer(self):
        return True
                
    @api.multi
    def get_warehouse_for_ict(self):
        self.ensure_one()
        warehouse = self.destination_warehouse_id
        return warehouse           
                
