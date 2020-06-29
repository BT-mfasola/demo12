# Copyright (c) 2017 Emipro Technologies Pvt Ltd (www.emiprotechnologies.com). All rights reserved.
from odoo import fields, models, api, _
class ResPartnerEpt(models.Model):
    _inherit = 'res.partner'
    street_no = fields.Char('Street No.')