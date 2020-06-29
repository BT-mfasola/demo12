from odoo import models, fields, api, _

class magento_instance(models.Model):
    _inherit = 'magento.instance'


    @api.multi    
    def import_AttributeList_scheduler(self, cron_mode=True):
        instance = self.search([])
        instance.import_att_list()
        return True

    @api.multi    
    def import_AttributeSet_scheduler(self, cron_mode=True):
        print("magento_v12_new_test",self)
        instance = self.search([])
        print("instanceinstance",instance)
        instance.import_att_set()
        return True

    @api.multi    
    def import_Category_scheduler(self, cron_mode=True):
        instance = self.search([])
        instance.import_cat()
        return True

    @api.multi    
    def import_product_scheduler(self, cron_mode=True):
        instance = self.search([])
        instance.import_products()
        return True

    @api.multi    
    def import_ProductImage_scheduler(self, cron_mode=True):
        instance = self.search([])
        instance.import_image()
        return True

    @api.multi    
    def import_Customer_scheduler(self, cron_mode=True):
        instance = self.search([])
        instance.import_customer()
        return True

    @api.multi    
    def import_Stock_scheduler(self, cron_mode=True):
        instance = self.search([])
        instance.import_stock()
        return True



    @api.multi    
    def export_Stock_scheduler(self, cron_mode=True):
        instance = self.search([])
        instance.export_stock()
        return True





    

class magento_shop(models.Model):
    _inherit = "magento.shop" 
    
    @api.multi    
    def import_Order_scheduler(self, cron_mode=True):
        shops = self.search([])
        for shop in shops:
            print("shopshop",shop)
            shop.import_orders()
        return True

    @api.multi
    def import_shipment_scheduler(self, cron_mode=True):
        shops = self.search([])
        for shop in shops:
            print("shopshop", shop)
            shop.import_shipment()
        return True

    @api.multi
    def import_invoice_scheduler(self, cron_mode=True):
        shops = self.search([])
        for shop in shops:
            print("shopshop", shop)
            shop.import_invoice()
        return True

    @api.multi    
    def export_Product_scheduler(self, cron_mode=True):
        shops = self.search([])
        if shops:
            shops[0].export_products()
        return True

    @api.multi    
    def export_Image_scheduler(self, cron_mode=True):
        shops = self.search([])
        if shops:
            shops[0].export_images()
        return True


    @api.multi    
    def update_OrderStatus_scheduler(self, cron_mode=True):
        shops = self.search([])
        for shop in shops:
            print("shopshop",shop)
            shop.export_order_status()
        return True

    
#     @api.multi    
#     def import_product_scheduler(self, cron_mode=True):
#         store_obj = self.env['sale.shop']
#         store_ids = store_obj.search([('amazon_shop','=',True),('auto_import_products','=',True)])
#         if store_ids:
#             store_ids.sorted(reverse=True)
#             store_ids.import_amazon_product()
#     return True
