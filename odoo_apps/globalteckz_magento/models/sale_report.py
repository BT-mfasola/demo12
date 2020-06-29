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
from odoo import tools

class sale_report(models.Model):
    _inherit = "sale.report"
    
    
    is_company = fields.Boolean(string='is_company', readonly=True)
    parent_id = fields.Many2one('res.partner',string='Parent Company',readonly=True)

    def _select(self):
        return  super(sale_report, self)._select() + ", c.is_company as is_company ,c.parent_id as parent_id"

    def  _from(self):
        return  super(sale_report, self)._from() + "left join res_partner c on (s.partner_id=c.id AND c.is_company=True)"

    def _group_by(self):
        return super(sale_report, self)._group_by() + " , c.is_company , c.parent_id"

