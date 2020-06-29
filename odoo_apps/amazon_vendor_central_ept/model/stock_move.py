from odoo import models, fields, api, _
from odoo.osv import osv

class stock_move(models.Model):
    _inherit = "stock.move"

    @api.multi
    def btn_action_cancel(self):
        return self.action_cancel()