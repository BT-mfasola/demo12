# Copyright (c) 2017 Emipro Technologies Pvt Ltd (www.emiprotechnologies.com). All rights reserved.
from openerp import fields, models, api, _
import re

class WizardSendToShip(models.TransientModel):
    _name = 'wizard.send.to.ship.ept'
    _description="DHL Send To Shipment Wizard"

    name1 = fields.Char('Name1')
    name2 = fields.Char('Name2')
    name3 = fields.Char('Name3 / Street2')
    dhl_recipient_add_method = fields.Selection([('dhl_street', ' Street'), ('dhl_packstation', ' Packstation'), ('dhl_filiale', ' Filiale'), ('dhl_parcelshop', ' Parcelshop')], 'Recipient Address Type', required=True, help="Select the Recipient address type and set method.", default="dhl_street")
    street_no = fields.Char('Number')
    post_no = fields.Char('Post Number')
    prefix = fields.Char('Prefix')
    street = fields.Char('Street')
    zip = fields.Char('Zip')
    city = fields.Char('City')
    res_email = fields.Char('E-mail')
    res_phone = fields.Char('Phone')
    country_id = fields.Many2one('res.country', string='Country')
    # use_more_package_flag = fields.Boolean(string="Visible and Invisible Use_more_address field using this field.", default=False)
    # use_more_pakages = fields.Boolean(string="Use Multiple Packages", help="When use the multiple packages set the value true, otherwise the value is false", default=False)
    picking_id = fields.Many2one('stock.picking',string="Picking")
    note = fields.Text('Description',help="Add an description that will be printed on the export label for International request.")
    @api.onchange("dhl_recipient_add_method")
    def onchange_dhl_recipient_add_method(self):
        """ Set the Recipient address when set the method...
            @param 
            @return: Set the Recipient address(value). 
            @author: Jigar v Vagadiya on dated 25-July-2017.
        """
        context = self._context
        shipping_active_id = self.env['stock.picking'].browse(context['active_ids'])[0]
        self.name1 = shipping_active_id.partner_id.name
        self.res_email = shipping_active_id.partner_id.email
        self.res_phone = shipping_active_id.partner_id.phone
       
        if shipping_active_id.carrier_id.delivery_type == 'dhl_de_ept':
            if self.dhl_recipient_add_method == 'dhl_street' :
                street_value = shipping_active_id.carrier_id.shipping_instance_id.dhl_street_no.name
                if street_value:
                    street_no = shipping_active_id.partner_id[street_value] 
                    street_no = street_no if street_no else ""
                    if street_no:
                        street_no = re.findall('\d+', street_no)
                        if street_no:
                            self.street_no = street_no[0]
                    if street_value == 'street':
                        street_no = shipping_active_id.partner_id[street_value] if shipping_active_id.partner_id[street_value] else ""
                        self.street = str(street_no.replace(self.street_no if self.street_no else "" or "", ""))
                    else:
                        self.street = shipping_active_id.partner_id.street
                    
            if self.dhl_recipient_add_method == 'dhl_packstation' :
                post_no_value = shipping_active_id.carrier_id.shipping_instance_id.dhl_packstation_postnumber.name
                prefix_value = shipping_active_id.carrier_id.shipping_instance_id.dhl_packstation_prefix
                street_value = shipping_active_id.carrier_id.shipping_instance_id.dhl_packstation_no.name
                if street_value:
                    self.street_no = shipping_active_id.partner_id[street_value]
                if post_no_value:
                    self.post_no = shipping_active_id.partner_id[post_no_value]
                if prefix_value:
                    self.prefix = prefix_value
            if self.dhl_recipient_add_method == 'dhl_filiale' :
                post_no_value = shipping_active_id.carrier_id.shipping_instance_id.dhl_filiale_postnumber.name
                prefix_value = shipping_active_id.carrier_id.shipping_instance_id.dhl_filiale_prefix
                street_value = shipping_active_id.carrier_id.shipping_instance_id.dhl_filiale_no.name
                if street_value:
                    self.street_no = shipping_active_id.partner_id[street_value]
                if post_no_value:
                    self.post_no = shipping_active_id.partner_id[post_no_value]
                if prefix_value:
                    self.prefix = prefix_value
            if self.dhl_recipient_add_method == 'dhl_parcelshop' :
                prefix_value = shipping_active_id.carrier_id.shipping_instance_id.dhl_parcelshop_prefix
                street_no_value = shipping_active_id.carrier_id.shipping_instance_id.dhl_parcelshop_no.name
                if street_no_value:
                    self.street_no = shipping_active_id.partner_id[street_no_value]
                if prefix_value:
                    self.prefix = prefix_value
        
#         address_additional_value=shipping_active_id.carrier_id.shipping_instance_id.additional_information.name
#         self.use_more_package_flag = shipping_active_id.carrier_id.shipping_instance_id.use_multiple_pakages
#         self.use_more_pakages = shipping_active_id.carrier_id.shipping_instance_id.use_multiple_pakages

        # self.use_more_package_flag = True
        # self.use_more_pakages = True
        self.name3 = shipping_active_id.partner_id.street2
#         self.street2=shipping_active_id.partner_id[address_additional_value]
        self.city = shipping_active_id.partner_id.city
        self.zip = shipping_active_id.partner_id.zip
        self.state_id = shipping_active_id.partner_id.state_id
        self.country_id = shipping_active_id.partner_id.country_id
    
    @api.multi
    def send_to_ship(self):
        """ Set the Recipient address when set the method...
            @param
            @return: Set the Recipient address(value).
            @author: Emipro Technologies Pvt Ltd
        """
        context = self._context
        if context.get('active_ids',False):
            shipping_active_id = self.env['stock.picking'].browse(context['active_ids'])[0]
            if shipping_active_id.carrier_id.delivery_type == 'dhl_de_ept':
                shipping_active_id.with_context(WizardSendToShip_id = self).send_to_shipper()
