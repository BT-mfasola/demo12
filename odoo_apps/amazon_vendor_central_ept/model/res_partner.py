from odoo import models,fields,api,_

class res_partner(models.Model):
    _inherit = 'res.partner'
    
    edi_gln_no = fields.Char('Amazon EDI GLN number')