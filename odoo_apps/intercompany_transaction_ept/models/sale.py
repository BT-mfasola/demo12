from odoo import api, fields, models, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    _description = 'Sale Order'
    
    intercompany_transfer_id = fields.Many2one('inter.company.transfer.ept', string="ICT", copy=False)


    """
    This Method is used to invoice journal issue when it is creating time(as breadcrumb)
    """
    @api.multi
    def _prepare_invoice(self):
        if self.intercompany_transfer_id:
            journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
            vals = super(SaleOrder, self.with_context({'journal_id':journal_id}))._prepare_invoice()
            return vals
        else:
            vals = super(SaleOrder, self)._prepare_invoice()
            return vals