from odoo import models, fields, api

class mismatch_data_ept(models.TransientModel):
    _name = 'mismatch.data.ept'
    _order = 'id desc'
    _description = "Records Not Found"

    mismatch_lines = fields.One2many('mismatch.line.ept','mismatch_id', string='Mismatch Lines')
    warehouse_ids = fields.Many2many('stock.warehouse',string='Warehouse')

    @api.multi
    def wizard_view(self):
        title = 'Missing Forecasted Data'
        view = self.env.ref('inventory_coverage_report_ept.mismatch_data_ept_form_view')

        return {
            'name': title,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mismatch.data.ept',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.ids[0],
            'context': self.env.context,
        }
        
class mismatch_line_ept(models.TransientModel):
    _name = 'mismatch.line.ept'
    _order = 'product_id,warehouse_id,period_id,id desc'
    _description = 'Mismatch Data Lines'
    
    mismatch_id = fields.Many2one('mismatch.data.ept', string='Mismatch Data')
    product_id = fields.Many2one('product.product', string='Product')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    period_id = fields.Many2one('requisition.period.ept', string='Period')