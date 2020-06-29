from odoo import fields, models, api

class RequisitionSummaryLine(models.Model):
    _name = 'requisition.summary.line.ept'
    _description = "Reorder Summary"
    
    supplier_rule_satisfied = fields.Boolean(string='Supplier Rule Satisfied')
    
    requisition_qty = fields.Integer(string='Demanded Quantity')
    minimum_requisition_qty = fields.Integer(string='Minimum Order Quantity')
    po_qty = fields.Integer(string='Purchase Order Quantity')
    
    product_id = fields.Many2one('product.product', string='Product', index=True)
    requisition_process_id = fields.Many2one('requisition.process.ept', string='Reorder Process', index=True)
    requisition_process_line_ids = fields.One2many('requisition.process.line.ept', 'requisition_summary_id', string='Process Lines')
    
    @api.onchange('po_qty')
    def get_minimum_requisition_qty(self):
        if self.product_id:
            seller = self.product_id._select_seller(quantity=self.po_qty)
            self.minimum_requisition_qty = seller.min_qty
        
