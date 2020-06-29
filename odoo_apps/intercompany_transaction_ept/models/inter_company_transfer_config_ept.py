from odoo import models, fields, api, _
from odoo.exceptions import Warning 

class InterCompanyTransferConfig(models.Model):    
    _name = "inter.company.transfer.config.ept"
    _rec_name = "sequence_id"
    _description = 'Inter Company Transfer Config'
    
    @api.model
    def _default_company(self):
        return self.env.user.company_id.id
    
    description = fields.Char("Discription")
    
    filter_refund = fields.Selection([('refund', 'Create a draft credit note'), ('cancel', 'Cancel: create credit note and reconcile')], default='refund', string='Refund Method', help='Refund base on this type. You can not Modify and Cancel if the invoice is already reconciled')
    
    auto_confirm_orders = fields.Boolean('Auto Confirm Orders')
    auto_create_invoices = fields.Boolean('Auto Create Invoices')
    auto_validate_invoices = fields.Boolean('Auto Validate Invoices')
    
    sequence_id = fields.Many2one('ir.sequence', 'Sequence')
    company_id = fields.Many2one('res.company', string='Company', readonly=True, compute=_default_company, store=True)
    
   

    
    @api.multi
    def unlink(self):
        raise Warning(_("You can not delete this record"))
