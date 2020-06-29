from odoo import fields, models

class ResCompany(models.Model):
    _inherit = "res.company"
    _description = 'Res Company'

    intercompany_user_id = fields.Many2one('res.users', string="Intercompany User")    
    sale_journal = fields.Many2one('account.journal', string="Sale Journal")
    purchase_journal = fields.Many2one('account.journal', string="Purchase Journal")
