from odoo import fields, models, api

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    _description = 'Purchase Order'
    
    requisition_process_id = fields.Many2one('requisition.process.ept', string='Reorder Process', index=True, copy=False)
    warehouse_requisition_process_id = fields.Many2one('warehouse.requisition.process.ept', string='Procurement Process')
    requisition_configuration_line_ids = fields.One2many('requisition.configuration.line.ept', 'purchase_order_id', string="Reorder Plannings")
    
class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    _description = 'Purchase Order Line'
    
    
    @api.onchange('product_id')
    def onchange_product_id(self):
        result = super(PurchaseOrderLine, self).onchange_product_id()
        if self._context.get('from_requisition_process') :
            fpos = self.order_id.fiscal_position_id
            company_id = self.order_id.company_id.id
            self.taxes_id = fpos.map_tax(self.product_id.supplier_taxes_id.filtered(lambda r: r.company_id.id == company_id))
        return result
    
