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

class delivery_carrier(models.Model):
    _name = "delivery.carrier"
    _inherit = "delivery.carrier"


    mage_delivery = fields.Boolean(string='Delivery')
    magento_code = fields.Char('Magento Code', size=64)
    magento_export = fields.Char('Magento Export', size=64)
    
    

delivery_carrier()