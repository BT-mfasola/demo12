# Copyright (c) 2017 Emipro Technologies Pvt Ltd (www.emiprotechnologies.com). All rights reserved.
from odoo import fields, models, api, _


class ShippingInstanceEptClass(models.Model):
    _inherit = 'shipping.instance.ept'

    provider = fields.Selection(selection_add=[('dhl_de_ept', 'DHL DE')])
    userid = fields.Char("DHL UserId", copy=False,
                         help="When use the sandbox account developer id use as the userId.When use the live account application id use as the userId.")
    password = fields.Char("DHL Password", copy=False,
                           help="When use the sandbox account developer portal password use to as the password.When use the live account application token use to as the password.")

    http_userid = fields.Char("HTTP UserId", copy=False, help="HTTP Basic Authentication.")
    http_password = fields.Char("HTTP Password", copy=False, help="HTTP Basic Authentication.")
    dhl_ekp_no = fields.Char("EKP Number", copy=False,
                             help="The EKP number sent to you by DHL and it must be maximum 10 digit allow.")

    #   There are configure when create the DHL shipping Instance
    dhl_street_no = fields.Many2one('ir.model.fields', string='Street No.',
                                    domain="[('model','=','res.partner'),('ttype','=','char')]",
                                    help="Street number is require when use defualt address.")
    dhl_packstation_postnumber = fields.Many2one('ir.model.fields', string='DHL Packstation Post Number',
                                                 domain="[('model','=','res.partner'),('ttype','=','char')]",
                                                 help="Post Number of the receiver, if not set receiver e-mail and/or mobilephone number needs to be set.")
    dhl_packstation_prefix = fields.Char("DHL Packstation Prefix", help="Packstation Prefix.")
    dhl_packstation_no = fields.Many2one('ir.model.fields', string='DHL Packstation No.',
                                         domain="[('model','=','res.partner'),('ttype','=','char')]")
    dhl_filiale_postnumber = fields.Many2one('ir.model.fields', string='DHL Filiale Post Number',
                                             domain="[('model','=','res.partner'),('ttype','=','char')]",
                                             help="Post Number of the receiver, if not set receiver e-mail and/or mobilephone number needs to be set.")
    dhl_filiale_prefix = fields.Char("DHL Filiale Prefix", help="Postfiliale Prefix")
    dhl_filiale_no = fields.Many2one('ir.model.fields', string='DHL Filiale No.',
                                     domain="[('model','=','res.partner'),('ttype','=','char')]",
                                     help="Postfiliale number,max length is 3.")
    dhl_parcelshop_prefix = fields.Char("Prefix", help="ParcelShop Prefix")
    dhl_parcelshop_no = fields.Many2one('ir.model.fields', string='No.',
                                        domain="[('model','=','res.partner'),('ttype','=','char')]",
                                        help="ParcelShop number,max length is 3.")

    _sql_constraints = [('user_unique', 'unique(userid)', 'User already exists!'),
                        ('ekp_no', 'unique(dhl_ekp_no)', 'EKP number already exists!'),
                        ('http_userid', 'unique(http_userid)', 'HTTP userId already exists!')]

    @api.one
    def dhl_de_ept_retrive_shipping_services(self, to_add):
        """ Retrive shipping services from the DHL
            @param:
            @return: list of dictionaries with shipping service
            @author: Jigar Vagadiya on dated 06-July-2017
        """
        shipping_services_obj = self.env['shipping.services.ept']
        services_name = {'V01PAK': 'DHL PAKET',
                         'V06PAK': 'DHL PAKET the same day',
                         'V53WPAK': 'DHL PAKET International',
                         'V54EPAK': 'DHL Europaket',
                         'V06WZ': 'Courier desired time',
                         'V06TG': 'Courier the same day',
                         'V86PARCEL': 'DHL PAKET Austria',
                         'V87PARCEL': 'DHL PAKET Connect',
                         'V82PARCEL': 'DHL PAKET International'}
        services = shipping_services_obj.search([('shipping_instance_id', '=', self.id)])
        services.unlink()
        # Display Services
        for company in self.company_ids:
            for service in services_name:
                global_code_condition = shipping_services_obj.search(
                    [('service_code', '=', service), ('shipping_instance_id', '=', self.id)])
                if global_code_condition:
                    if shipping_services_obj.search([('company_ids', '=', company.id), ('service_code', '=', service),
                                                     ('shipping_instance_id', '=', self.id)]):
                        return True
                    else:
                        global_code_condition.write({'company_ids': [(4, company.id)]})
                else:
                    vals = {'shipping_instance_id': self.id, 'service_code': service,
                            'service_name': services_name.get(service, False), 'company_ids': [(4, company.id)]}
                    shipping_services_obj.create(vals)

    @api.multi
    def dhl_de_ept_quick_add_shipping_services(self, service_type, service_name):
        """ Allow you to get the default shipping services value while creating quick 
            record from the Shipping Service for DHL
            @param service_type: Service type of DHL
            @return: dict of default value set
            @author: Jigar Vagadiya on dated 3-april-2017
        """
        return {'default_name': service_name,
                'default_services_name': service_type,
                'default_dhl_ekp_no': self.dhl_ekp_no
                }

    @api.multi
    def write(self, vals):
        """ Override write method and write the EKP number for all delivery method as per instance. 
            @param 
            @return: set ekp number for all delivery method.
            @author: Jigar Vagadiya on dated 24-Aug-2017.
        """
        res = super(ShippingInstanceEptClass, self).write(vals)
        delivery_carrier_obj = self.env['delivery.carrier']
        delivery_methods = delivery_carrier_obj.search(
            [('shipping_instance_id', '=', self.id), ('delivery_type', '=', self.provider)])
        if delivery_methods:
            delivery_methods.write({'dhl_ekp_no': self.dhl_ekp_no})
        return res
