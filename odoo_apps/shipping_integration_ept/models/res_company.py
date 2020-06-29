# Copyright (c) 2017 Emipro Technologies Pvt Ltd (www.emiprotechnologies.com). All rights reserved.
from odoo import models, fields, api

class ResCompany(models.Model):
    _inherit = "res.company"

    def _default_uom_setting(self):
        weight_uom_id = self.env.ref('uom.product_uom_kgm', raise_if_not_found=False)
        if not weight_uom_id:
            uom_categ_id = self.env.ref('uom.product_uom_categ_kgm').id
            weight_uom_id = self.env['uom.uom'].search([('category_id', '=', uom_categ_id), ('factor', '=', 1)], limit=1)
        return weight_uom_id


    weight_unit_of_measurement_id=fields.Many2one('uom.uom',string="Weight Unit Of Measurement",help="Unit of measure for item weight",default=_default_uom_setting)
