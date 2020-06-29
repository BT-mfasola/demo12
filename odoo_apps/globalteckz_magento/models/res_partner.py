# -*- coding: utf-8 -*-
##############################################################################
#                                                                            #
#    Globalteckz Software Solutions and Services                             #
#    Copyright (C) 2013-Today(www.globalteckz.com).                          #
#                                                                            #
#    This program is free software: you can redistribute it and/or modify    #
#    it under the terms of the GNU Affero General Public License as          #
#    published by the Free Software Foundation, either version 3 of the      #
#    License, or (at your option) any later version.                         #
#                                                                            #
#    This program is distributed in the hope that it will be useful,         #  
#    but WITHOUT ANY WARRANTY; without even the implied warranty of          #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the           #
#    GNU Affero General Public License for more details.                     #
#                                                                            #
#                                                                            #
##############################################################################

from odoo import models, fields, api, _
import datetime
from datetime import date, timedelta

class res_partner(models.Model):
   
    _inherit = "res.partner"

 
    customer_grp = fields.Many2one('customer.group','Customer Group')
    contact_name = fields.Char('Contact Name',size=100)
    mage_cust_id = fields.Char('Customer ID',size=100)
    mage_adds_id = fields.Char('Address ID',size=100)
    dob=fields.Date('Date Of Birth')
    tax_vat=fields.Char('Tax /Vat Number')
    is_a_magento_customer=fields.Boolean(string="Is a Magento Customer")
    partner_id = fields.Many2one('res.partner', string="Partner")
    instance_id = fields.Many2one('magento.instance', string='Magento Instance')

res_partner()