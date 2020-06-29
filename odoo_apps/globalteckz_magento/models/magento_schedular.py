from odoo import api, fields, models, _
from datetime import timedelta, datetime
from odoo import netsvc
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class magento_shop(models.Model):
    _inherit = "magento.shop"


    @api.multi
    def import_product_scheduler(self, cron_mode=True):
        instance_obj = self.env['magento.instance']
        instance_id = instance_obj.search([])
        instance_id.import_products()
        return True
        
    @api.multi    
    def import_orders_scheduler(self, cron_mode=True):
        print( "order ...schedulerrrrrrr ")
        shop_obj = self.env['magento.shop']
        shop_id = shop_obj.search([])
        shop_id.import_orders()
        return True
      
        
    @api.multi    
    def export_orders_status_scheduler(self, cron_mode=True):
        print ("order ...schedulerrrrrrr ")
        shop_obj = self.env['magento.shop']
        shop_id = shop_obj.search([])
        shop_id.export_order_status()
        return True
        
        
    @api.multi    
    def import_customer_scheduler(self, cron_mode=True):
        print ("customer ...schedulerrrrrrr ")
        instance_obj = self.env['magento.instance']
        instance_id = instance_obj.search([])
        instance_id.import_customer_group()
        instance_id.import_customer()
        return True
        
        
        
        
        
        
        
        
