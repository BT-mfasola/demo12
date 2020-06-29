from odoo import models, fields, api, _

class Amazon_Seller_Location_Code(models.Model):
    _name = 'amazon.seller.location.code'

    name = fields.Char(string='Seller')
    gln_number = fields.Char(string='GLN Number')
    description = fields.Char(string='Description')
