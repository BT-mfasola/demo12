from odoo import models,fields,api,_
from odoo.exceptions import Warning

class stock_warehosue(models.Model):
    _inherit = 'stock.warehouse'
    
    vendor_id = fields.Many2one('amazon.vendor.instance',string = 'Amazon Vendor')
    gln_number = fields.Char(string = "GLN Number")