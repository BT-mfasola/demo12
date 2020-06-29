from odoo import fields, api, models , _

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    _description = 'Purchase Order'
    
    intercompany_transfer_id = fields.Many2one('inter.company.transfer.ept', string="ICT", copy=False)
