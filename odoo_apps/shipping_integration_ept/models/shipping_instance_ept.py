# Copyright (c) 2017 Emipro Technologies Pvt Ltd (www.emiprotechnologies.com). All rights reserved.
import ast
from math import ceil

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError,Warning


class ShippingInstanceEpt(models.Model):
    _name = "shipping.instance.ept"
    _description = 'Shipping Instance Configuration'


    @api.multi
    def _compute_in_test_delivery_method_count(self):
        """Compute the Test Delivery method in delivery carrier.
            @param: None.
            @return: Count the Test delivery method.
            @author: Jigar vagadiya on dated 21 nov 2017.
        """
        delivery_carrier_obj = self.env['delivery.carrier']
        for instance in self:
            delivery_methods = delivery_carrier_obj.search([('shipping_instance_id','=',instance.id),('prod_environment','=',False)])
            instance.in_test_delivery_method_count = len(delivery_methods.ids)
    
    @api.multi
    def _compute_in_prod_delivery_method_count(self):
        """Compute the production Delivery method in delivery carrier.
            @param: None.
            @return: Count the production delivery method.
            @author: Jigar vagadiya on dated 21 nov 2017.
        """
        delivery_carrier_obj = self.env['delivery.carrier']
        for instance in self:
            delivery_methods = delivery_carrier_obj.search([('shipping_instance_id','=',instance.id),('prod_environment','=',True)])
            instance.in_prod_delivery_method_count = len(delivery_methods.ids)
    
    @api.multi
    def _compute_delivery_method(self):
        """Display Inactive and active delivery method in shipping instance.
            @param: None.
            @return: Display the active and inactive delivery method.
            @author: Jigar vagadiya on dated 1-May-2017
        """
        delivery_carrier_obj = self.env['delivery.carrier']
        delivery_methods = delivery_carrier_obj.search([('shipping_instance_id','=',self.id),('delivery_type','=',self.provider)])
        self.active_delivery_method =len(delivery_methods)
        inactive_delivery_methods = delivery_carrier_obj.search([('shipping_instance_id','=',self.id),('delivery_type','=',self.provider),('active','=',False)])
        self.inactive_delivery_method =len(inactive_delivery_methods)
    
    name = fields.Char(required=True,help="Shipping instance name.",string="Name")
    color = fields.Integer(string='Color Index',help="select color")
    in_test_delivery_method_count = fields.Integer(compute='_compute_in_test_delivery_method_count', string="Test")
    in_prod_delivery_method_count = fields.Integer(compute='_compute_in_prod_delivery_method_count', string="Production")
    provider = fields.Selection(selection=[], string='Provider', required=True,help="Select shipping provider name.")    
    image_instance = fields.Binary(string="Image",help="Select Image.")
    company_ids = fields.Many2many('res.company', string="Companies", required=True, default=lambda self: self.env.user.company_id,help="When require multiple companies than select useful companies.")
    service_ids = fields.One2many('shipping.services.ept', 'shipping_instance_id', string="Services",help="Bellow services provided By Provider.")
    active = fields.Boolean('Active', help="If the active field is set to False, then can not access the Instance.", default=True)
    active_delivery_method = fields.Integer(compute='_compute_delivery_method')
    inactive_delivery_method = fields.Integer(compute='_compute_delivery_method')
    tracking_link=fields.Char(string="Tracking Link",help="Tracking link(URL) useful to track the shipment or package from this URL.",size=256)
    #automatic_manage_package=fields.Boolean(help="If field is set to True, then manage the package automaticlly.",string="Manage The Package")
    mail_template_id = fields.Many2one('mail.template', 'E-mail Template')
    is_automatic_shipment_mail = fields.Boolean('Automatic Send Shipment Confirmation Mail')

    @api.one
    def retrive_shipping_services(self,to_add):
        """ Retrieve shipping services from the service provider
            @param: Receiver Address.
            @return: list of dictionaries with shipping service.
            @author: Jignesh Jarsaniya on dated 25-March-2017.
        """
        self.ensure_one()
        if hasattr(self, '%s_retrive_shipping_services' % self.provider):
            return getattr(self, '%s_retrive_shipping_services' % self.provider)(to_add)

    def action_view_delivery_method(self):
        action = self.env.ref('delivery.action_delivery_carrier_form').read()[0]
        action['domain'] = [('shipping_instance_id','=',self.id)]
        action['context'] = {'default_shipping_instance_id': self.id, 'default_delivery_type' : self.provider}
        return action

    @api.multi
    def navigate_to_test_delivery_method(self):
        """ Retrieve shipping services those are in test environment from kanban view.
            @param: None.
            @return: Action of delivery carrier if found else False
            @author: Jignesh Jarsaniya on dated 31-March-2017
        """
        context_default = dict(self.env.context or {})
        context_default.update({'default_shipping_instance_id' : self.id,
                            'default_delivery_type' : self.provider,})
        if hasattr(self, '%s_quick_add_shipping_services' % self.provider) and self.service_ids[0].service_code if self.service_ids else "":
                context_default.update(getattr(self, '%s_quick_add_shipping_services' % self.provider)(self.service_ids[0].service_code if self.service_ids else "", self.service_ids[0].service_name if self.service_ids else ""))
        
        self.ensure_one()
        action = self.env.ref('delivery.action_delivery_carrier_form') or False
        if action :
            result = action.read()[0] or {}
            domain = result.get('domain') and ast.literal_eval(result.get('domain')) or []
            context = result.get('context') and ast.literal_eval(result.get('context')) or {}
            domain.append(('shipping_instance_id','=',self.id))
            domain.append(('prod_environment', '=', False))
            context.update({'search_default_in_test':1})
            result['domain'] = domain

            result['context'] = context
            result['context'] = context_default
            return result
        return False

    @api.multi
    def navigate_to_production_delivery_method(self):
        """ Retrieve shipping services those are in production environment from kanban view.
            @param: None.
            @return: Action of delivery carrier if found else False
            @author: Jignesh Jarsaniya on dated 01-April-2017
        """
        context_default = dict(self.env.context or {})
        context_default.update({'default_shipping_instance_id' : self.id,
                            'default_delivery_type' : self.provider,})
        if hasattr(self, '%s_quick_add_shipping_services' % self.provider) and self.service_ids[0].service_code if self.service_ids else "":
                context_default.update(getattr(self, '%s_quick_add_shipping_services' % self.provider)(self.service_ids[0].service_code if self.service_ids else "", self.service_ids[0].service_name if self.service_ids else ""))
        
        self.ensure_one()
        action = self.env.ref('delivery.action_delivery_carrier_form') or False
        if action :
            result = action.read()[0] or {}
            domain = result.get('domain') and ast.literal_eval(result.get('domain')) or []
            context = result.get('context') and ast.literal_eval(result.get('context')) or {}
            domain.append(('shipping_instance_id','=',self.id))
            domain.append(('prod_environment', '=', True))
            context.update({'search_default_in_production':1})
            result['domain'] = domain
            result['context'] = context
            result['context'] = context_default
            return result
        return False        
     
    @api.multi
    def unlink(self):
        """Delete the Shipping instance
            @param: None
            @return: Delete the Shipping Instance.
            @author: Jigar vagadiya on dated 24-April-2017
        """
        delivery_carrier_obj = self.env['delivery.carrier']
        for instance in self:
            delivery_methods = delivery_carrier_obj.search([('shipping_instance_id','=',instance.id)])
            inactive_delivery_methods = delivery_carrier_obj.search([('shipping_instance_id','=',instance.id),('active','=',False)])
            if delivery_methods or inactive_delivery_methods:
                raise Warning(_("You can not delete %s shipping instance because method is exist.") % instance.name)
        return super(ShippingInstanceEpt,self).unlink()
    
    @api.multi
    def toggle_active(self):
        """Active and Inactive the Shipping instance and Delivery Method.
            @param: None
            @return: Active and Inactive the Shipping instance and Delivery Method.
            @author: Jigar vagadiya on dated 26-April-2017
        """
        delivery_carrier_obj = self.env['delivery.carrier']
        delivery_methods = delivery_carrier_obj.search([('shipping_instance_id','=',self.id)])
        if delivery_methods:
            delivery_methods.write({'active':False}) 
        for record in self:
            record.active = not record.active