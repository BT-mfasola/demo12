from odoo import fields, models, api

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    _description = 'Account Invoice'
    
    warehouse_requisition_process_id = fields.Many2one('warehouse.requisition.process.ept', string='Procurement Process')
