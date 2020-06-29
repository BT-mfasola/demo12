# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.


from odoo import models, fields, api

class RiskCategory(models.Model):
    _name = "project.risk.category"

    name = fields.Char(
        string='Name',
        required=True,
    )
    code = fields.Char(
        string='Code',
        required=True,
    )
    notes = fields.Text(
        string='Internal Notes',
        copy=True,
    )
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: