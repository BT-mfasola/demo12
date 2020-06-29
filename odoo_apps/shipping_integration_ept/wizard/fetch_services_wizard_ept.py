# Copyright (c) 2017 Emipro Technologies Pvt Ltd (www.emiprotechnologies.com). All rights reserved.
from odoo import models, fields, api,_
class FetchServicesWizardEpt(models.TransientModel):
    _name = "fetch.services.wizard.ept"
    _description="Retrieve Service Wizard"
    
    #Specific Address Wise service
    use_toaddress_different = fields.Boolean(string="Use ToAddress Different",help="If ToAddress true then provider is provide the services using the ToAddress.",default=False)
    #To address Field.
    to_street = fields.Char('Street')
    to_street2 = fields.Char('Street2')
    to_zip = fields.Char('Zip', change_default=True)
    to_city = fields.Char('City')
    to_state_id = fields.Many2one("res.country.state", string='State')
    to_country_id = fields.Many2one('res.country', string='Country')
        
    @api.multi
    def fetch_shipping_services(self):
        context = self._context
        if context.get('active_ids', False):
            shipping_active_id = self.env['shipping.instance.ept'].browse(context['active_ids'])[0]
            shipping_active_id.retrive_shipping_services(self)
        return {
            'effect': {
                'fadeout': 'slow',
                'message': "Yeah! Shipping services has been retrieved.",
                'img_url': '/web/static/src/img/smile.svg',
                'type': 'rainbow_man',
            }
        }
