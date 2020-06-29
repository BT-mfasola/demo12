from odoo import fields, models, api, _

class Saleorder(models.Model):
    _inherit = 'sale.order'
    _description = 'Sale Order'
    
    warehouse_requisition_process_id = fields.Many2one('warehouse.requisition.process.ept', string='Procurement Process')
    
