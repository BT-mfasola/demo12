# Copyright (c) 2017 Emipro Technologies Pvt Ltd (www.emiprotechnologies.com). All rights reserved.
from odoo import fields, models, api, _
class ResCompanyEpt(models.Model):
    _inherit = 'res.company'
    street_no = fields.Char('Street No.')