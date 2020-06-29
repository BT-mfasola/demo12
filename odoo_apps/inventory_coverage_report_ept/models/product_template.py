from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = "product.template"
    
    warehouse_ids = fields.Many2many('stock.warehouse', string='Warehouses')
    can_be_used_for_coverage_report_ept = fields.Boolean(string="Can Be Used For Coverage Report?", default=True)
