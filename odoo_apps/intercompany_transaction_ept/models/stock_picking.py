from odoo import fields, api, models, _

class Picking(models.Model):
    _inherit = 'stock.picking'
    _description = 'Stock Picking'
    
    intercompany_transfer_id = fields.Many2one('inter.company.transfer.ept', string="ICT", copy=False)

    @api.model
    def create(self, vals):
        res = super(Picking, self).create(vals)
        order_id = self.env['sale.order'].search([('name', '=', res.origin)])
        if not order_id:
            order_id = self.env['purchase.order'].search([('name', '=', res.origin)])
        if order_id and order_id.intercompany_transfer_id:
            res.intercompany_transfer_id = order_id.intercompany_transfer_id.id
        return res

    @api.multi
    def _create_backorder(self):
        res = super(Picking, self)._create_backorder()
        for backorder in res:
            if backorder.backorder_id and backorder.backorder_id.intercompany_transfer_id:
                backorder.write({"intercompany_transfer_id":backorder.backorder_id.intercompany_transfer_id.id})
        return res