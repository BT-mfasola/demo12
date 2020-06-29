# Copyright (c) 2017 Emipro Technologies Pvt Ltd (www.emiprotechnologies.com). All rights reserved.

from odoo import models, fields, api, _

class ShippingServicesEpt(models.Model):
    _name="shipping.services.ept"
    _description = 'Retrieve Shipping Services'
    
    shipping_instance_id=fields.Many2one('shipping.instance.ept',string="Shipping Services", required=True, ondelete="cascade")
    service_code = fields.Char(string="Service Code")
    service_name=fields.Char(string="Service Name")
    company_ids=fields.Many2many('res.company',string="Companies",required=True)
    
    @api.multi
    def add_new_shipping_service(self):
        self.ensure_one()
        shipping_instance_obj = self.env['shipping.instance.ept']
        context = dict(self.env.context or {})
        view = self.env.ref('delivery.view_delivery_carrier_form')
        if view :
            context.update({'default_shipping_instance_id' : self.shipping_instance_id.id,
                            'default_delivery_type' : self.shipping_instance_id.provider,})
            if hasattr(shipping_instance_obj, '%s_quick_add_shipping_services' % self.shipping_instance_id.provider) and self.service_code :
                context.update(getattr(shipping_instance_obj, '%s_quick_add_shipping_services' % self.shipping_instance_id.provider)(self.service_code,self.service_name))
            return {
                'name': _('Add Delivery Method'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'delivery.carrier',
                'view_id': view.id,
                'type': 'ir.actions.act_window',
                'context': context,
                'target': 'current'
            }