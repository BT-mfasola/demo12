from odoo import models, fields, api, _

class Delivery_Carrier(models.Model):
    _inherit = 'delivery.carrier'

    carrier_reference_number = fields.Char(string = "Carrier's reference number")