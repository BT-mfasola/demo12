# Copyright (c) 2017 Emipro Technologies Pvt Ltd (www.emiprotechnologies.com). All rights reserved.
from odoo import models, fields, api
class ProductTemplate(models.Model):
    _inherit = "product.template"

    weight_unit_measurement_id=fields.Many2one('uom.uom',string="Weight Unit Of Measurement",help="Unit of measure for item weight",related="company_id.weight_unit_of_measurement_id",readonly=True)

# class ProductProduct(models.Model):
#     _inherit = "product.product"
#
#     weight_unit_measurement_id=fields.Many2one('uom.uom',string="Weight Unit Of Measurement",help="Unit of measure for item weight",related="company_id.weight_unit_of_measurement_id",readonly=True)
