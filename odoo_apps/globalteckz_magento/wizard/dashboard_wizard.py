import time
from odoo import api, fields, models


class MagentoConnectorWizard(models.Model):
    _name = "magento.connector.wizard"
    
    shop_ids = fields.Many2one('magento.shop', string="Select Shops", readonly=True)
    instance_ids = fields.Many2one('magento.instance',string='Select Instance')
    
    import_orders = fields.Boolean('Import Orders')
    import_products = fields.Boolean('Import Products')
    import_product_attributes = fields.Boolean('Import Products Attributes',help="Includes Product Attributes and Categories")
    import_inventory = fields.Boolean('Import Inventory')
    import_categories=fields.Boolean("Import Categories")
    import_product_images=fields.Boolean("Import Product Images")
    import_attribute_sets=fields.Boolean("Import Attribute Sets")
    
    update_order_status=fields.Boolean("Update Categories")
    update_product=fields.Boolean('Update Product')
    
    export_products = fields.Boolean('Export Products')
    export_images = fields.Boolean('Export Images')
    export_inventory = fields.Boolean('Export Inventory')
    export_link_products = fields.Boolean('Export Link Products')
    import_order_date = fields.Datetime(string='Date')

    @api.model
    def default_get(self, fields):
        rec = super(MagentoConnectorWizard, self).default_get(fields)
        rec.update({
            'shop_ids':self._context.get('active_ids')[0]
            })
        return rec
    
  
    @api.one
    def import_magento(self):
        shop_obj = self.env['magento.shop']
        context = dict(self._context or {})
        active_id = context.get('active_ids')
        shop_id = shop_obj.browse(active_id)
        instance_ids=self.instance_ids
        if self.import_attribute_sets == True:
            instance_ids.import_att_set()
        if self.import_product_attributes == True:
            instance_ids.import_att_list()
        if self.import_categories == True:
            instance_ids.import_cat()
            
        if self.import_products == True:
            instance_ids.import_products()
            
        if self.import_inventory == True:
            instance_ids.import_stock()
            
        if self.import_product_images == True:
            instance_ids.import_image()
            
        if self.import_orders == True and self.import_order_date:      
            shop_id.import_orders_dashboard(self.import_order_date)
                 
        if self.update_order_status == True:        
            shop_id.export_order_status() 
                  
        if self.update_product == True:     
            shop_id.export_products()  
                     
        if self.export_products == True:        
            shop_id.export_new_products() 
                  
        if self.export_images == True:      
            shop_id.export_images()     
            
        if self.export_inventory == True:       
            instance_ids.export_stock()   
              
        if self.export_link_products == True:       
            shop_id.export_link_products()      
        return True
        
#         if self.import_product_attributes:
#             for shop_id in shop_ids:
#                 shop_id.import_product_attributes()
#                
#        if self.import_inventory:
#            for shop_id in shop_ids:
#                shop_id.import_product_inventory()
#                
#        if self.import_orders:
#            for shop_id in shop_ids:
#                shop_id.import_orders()
#        
#        if self.import_messages:
#            for shop_id in shop_ids:
#                shop_id.import_messages()
#                
#        if self.import_cart_rules:
#            for shop_id in shop_ids:
#                shop_id.import_cart_rules()
#        
#        if self.import_catalog_rules:
#            for shop_id in shop_ids:
#                shop_id.import_catalog_price_rules()
#                                        
#        if self.update_product_data:
#            for shop_id in shop_ids:
#                list_ids=self.env['product.listing'].search([('shop_id','>=',shop_id.id)])
#                product_ids=[list_id.product_id.id for list_id in list_ids if list_id.product_id]
#                presta_instance_id=shop_id.prestashop_instance_id
#                self.env['prestashop.upload.products'].create({}).upload_products(False,product_ids,presta_instance_id.id)
#        
#        if self.update_order_status:
#            for shop_id in shop_ids:
#                sale_ids=self.env['sale.order'].search([('shop_id','=',shop_id.id),('state','not in',('cancel','draft','sent'))])
#                sale_ids=[sale_id.id for sale_id in sale_ids]
#                presta_instance_id=shop_id.prestashop_instance_id
#                self.env['prestashop.upload.orders'].create({}).upload_orders(False,sale_ids,presta_instance_id)
#        
#        if self.update_categories:
#            for shop_id in shop_ids:
#                presta_instance_id=shop_id.prestashop_instance_id
#                prestashop=self.env['sale.shop'].browse(presta_instance_id.id).presta_connect_json()
#                categ_list=self.env['prestashop.category'].search([('shop_id','=',shop_id.id)])
##                 categ_list=[categ_id.id for categ_id in categ_list]
#                self.env['prestashop.upload.products'].upload_categories(prestashop,categ_list)        
#        
#        if self.update_cart_rules:
#            for shop_id in shop_ids:
#                cart_rule_ids=self.env['cart.rules'].search([('prestashop_id','=',shop_id.id)])
#                cart_rule_ids=[cart_id.id for cart_id in cart_rule_ids]
#                presta_instance_id=shop_id.prestashop_instance_id
#                self.env['upload.cart.rule'].create({}).upload_cart_rule(False,cart_rule_ids,presta_instance_id)
#        
#

        return True
    
    