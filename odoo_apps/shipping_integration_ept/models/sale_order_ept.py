from odoo import models, fields, api, _

class sale_order(models.Model):
    _inherit = "sale.order"

    estimated_arrival_date_ept = fields.Date(string='Estimated Arrival Date', help="Estimated Arrival Date describe the shipment will reach the destination location.",copy=False)