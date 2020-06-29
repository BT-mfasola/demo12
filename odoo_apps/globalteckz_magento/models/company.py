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
from odoo.tools .translate import _

class ResCompany(models.Model):
    """Override company to add images configuration"""
    _inherit = "res.company"
    
    local_media_repository = fields.Char(
                        'Images Repository Path',
                        size=256,
                        required=True,
                        help='Local mounted path on OpenERP server where all your images are stored.'
                    )
    

    def get_local_media_repository(self):
        if id:
            return self.local_media_repository
        user = self.env['res.users'].browse( uid)
        return user.company_id.local_media_repository

ResCompany()
