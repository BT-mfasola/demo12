# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api

class Risk(models.Model):
    _name = "project.risk"

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
    risk_quantification = fields.Selection(
        selection=[('low','Low'),
                    ('high','High'),
                    ('medium','Medium'),
                    ('critical','Critical')
        ],
        string='Risk Quantification',
    )
    category_id = fields.Many2one(
        'project.risk.category',
        'Category',
        required=True,
    )
    type_id = fields.Many2one(
        'project.risk.type',
        'Risk Type',
        required=True,
    )
    response_id = fields.Many2one(
        'project.risk.response',
        'Risk Response',
        required=True,
    )
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: