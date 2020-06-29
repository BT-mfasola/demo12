from odoo import fields, models, api, _

class WarehouseRequisitionSummaryLine(models.Model):
    _name = 'warehouse.requisition.summary.line.ept'
    _description = "Procurement Process Summary"
    
    is_sufficient_stock = fields.Boolean(string='Sufficient Stock')

    requisition_qty = fields.Integer(string='Demanded Quantity')
    available_qty = fields.Integer(string='Available Qty')
    deliver_qty = fields.Integer(string='Deliver Qty')
    
    product_id = fields.Many2one('product.product', string='Product', index=True)
    warehouse_requisition_process_id = fields.Many2one('warehouse.requisition.process.ept', string='Procurement Process')

    warehouse_requisition_process_line_ids = fields.One2many('warehouse.requisition.process.line.ept', 'warehouse_requisition_summary_id', string='Warehouse Process Lines')
