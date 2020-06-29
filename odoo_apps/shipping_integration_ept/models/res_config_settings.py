# Copyright (c) 2017 Emipro Technologies Pvt Ltd (www.emiprotechnologies.com). All rights reserved.
from odoo import api,fields, models
class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    product_weight_uom_id = fields.Many2one('uom.uom', string='Weight Unit Of Measurement')
    download_partial_invoice = fields.Boolean(default=False, string="Download Partial Invoices", help="Partial Invoice Available True Than Download Available Invoices.",copy=False)

    @api.multi
    def set_values(self):
        res=super(ResConfigSettings, self).set_values()
        company_id = self.company_id or self.env.user.company_id
        company_id.write({'weight_unit_of_measurement_id': self.product_weight_uom_id.id})
        return res
# give error when first time create database. because not set uom in compnay. Consider this thing.
    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        company_id = self.company_id or self.env.user.company_id
        res.update({'product_weight_uom_id': company_id.weight_unit_of_measurement_id and company_id.weight_unit_of_measurement_id.id})
        return res

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(download_partial_invoice=params.get_param('batch_pickings_validate_ept.download_partial_invoice',default=False))
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param("batch_pickings_validate_ept.download_partial_invoice", self.download_partial_invoice)
