# Copyright (c) 2017 Emipro Technologies Pvt Ltd (www.emiprotechnologies.com). All rights reserved.
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, Warning
class StockMove(models.Model):
    _inherit = 'stock.move'
    def _default_uom_ept(self):
        company_id = self.company_id or self.env.user.company_id
        if company_id and company_id.weight_unit_of_measurement_id:
            return company_id.weight_unit_of_measurement_id
        else:
            uom_categ_id = self.env.ref('uom.product_uom_categ_kgm').id
            return self.env['uom.uom'].search([('category_id', '=', uom_categ_id), ('factor', '=', 1)], limit=1)
    weight_uom_id = fields.Many2one('uom.uom', string='Weight Unit of Measure', required=True, readonly=True,
                                    help="Unit of Measure (Unit of Measure) is the unit of measurement for Weight",
                                    default=_default_uom_ept)


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    def _default_uom_ept(self):
        company_id = self.company_id or self.env.user.company_id
        if company_id and company_id.weight_unit_of_measurement_id:
            return company_id.weight_unit_of_measurement_id
        else:
            weight_uom_id = self.env.ref('uom.product_uom_kgm', raise_if_not_found=False)
            if not weight_uom_id:
                uom_categ_id = self.env.ref('uom.product_uom_categ_kgm').id
                weight_uom_id = self.env['uom.uom'].search([('category_id', '=', uom_categ_id), ('factor', '=', 1)],
                                                               limit=1)
            return weight_uom_id

    weight_uom_id = fields.Many2one('uom.uom', string='Unit of Measure', required=True, readonly="1",
                                    help="Unit of measurement for Weight", default=_default_uom_ept)

    is_shipment_confirmation_send = fields.Boolean('Shipment Confirmation Send')

    @api.multi
    def auto_shipment_confirm_mail(self):
        self.ensure_one()
        ctx = dict(self._context) or {}
        shipping_instance = self.carrier_id and self.carrier_id.shipping_instance_id or False
        if shipping_instance:
            email_template = shipping_instance.mail_template_id or False
            if not email_template:
                raise ValidationError(
                    _('You must set the value of E-mail Template in Menu Settings >> Shipping Provider.'))
            # tracking_link = self.open_website_url()
            # tracking_link = tracking_link.get('url', False)
            if self.carrier_id.get_tracking_link(self):
                tracking_link = self.carrier_id.get_tracking_link(self)
                ctx.update({'tracking_link': tracking_link})
                email_template.with_context(ctx).send_mail(self.id, True)
                self.write({'is_shipment_confirmation_send': True})
            else:
                raise ValidationError(
                    _('Tracking Link are not available please contact your Administrator.'))
        return True

    @api.multi
    def send_to_shipper(self):
        res = super(StockPicking, self).send_to_shipper()
        carrier = self.carrier_id or False
        if carrier and carrier.shipping_instance_id and carrier.shipping_instance_id.is_automatic_shipment_mail == True:
            self.auto_shipment_confirm_mail()
        return res
