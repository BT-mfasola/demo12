from odoo import api, models, fields , _

class AccountInvoice(models.Model):
    
    _inherit = 'account.invoice'
    _description = 'Account Invoice'

        
    intercompany_transfer_id = fields.Many2one('inter.company.transfer.ept', string="ICT", copy=False)
    
    @api.model
    def create(self, vals):
        res = super(AccountInvoice, self).create(vals)
        order_id = self.env['sale.order'].search([('name', '=', res.origin)])
        if not order_id:
            order_id = self.env['purchase.order'].search([('name', '=', res.origin)])
        if order_id and order_id.intercompany_transfer_id:
            res.intercompany_transfer_id = order_id.intercompany_transfer_id.id
        return res
