# -*- coding: utf-8 -*-
import logging
logger = logging.getLogger('amazon')

from odoo import api, fields, models, _

class MagentoLog(models.Model):
    _name='magento.log'
   
    name = fields.Char('name')
    description = fields.Char('Log Description')
    res_id = fields.Integer('Resource')
    create_date = fields.Datetime(string="Create Date")
    magento_log_details_id = fields.One2many('magento.log.details', 'magento_log_id', string='Magento Log Details')
    

class MagentoLogDetails(models.Model):
    _name='magento.log.details'
    
    
    name = fields.Char('name')
    description = fields.Char('Log Description')
    create_date = fields.Datetime(string="Create DateTime")
    magento_log_id = fields.Many2one('magento.log', string='Magento Log')
    
#     @api.model
#     def create(self, vals):
#         if not vals.get('name'):
#             vals['name']= self.env['ir.sequence'].next_by_code('amazon.log') or 'Log Sequence'
#         res = super(AmazonLog, self).create(vals)
#         return res
