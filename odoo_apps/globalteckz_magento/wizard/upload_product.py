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

from odoo.osv import fields, osv
#from magento_connector.PyMagento import Magento
from odoo.tools .translate import _

class export_active_products(osv.osv_memory):
    _name = "export.active.products"
    _description = "Uplod Active Product on Magento "
    
    def export_active_product(self, cr, uid, ids, context):
        shop_obj=self.pool.get('magento.shop')
        shop_id = shop_obj.search(cr,uid,[('magento_shop','=',True)])[0]
        shop_obj.export_products( cr, uid, [shop_id], context)
        return True
    
    def export_active_link_product(self, cr, uid, ids, context):
        shop_obj=self.pool.get('magento.shop')
        shop_id = shop_obj.search(cr,uid,[('magento_shop','=',True)])[0]
        shop_obj.export_link_products( cr, uid, [shop_id], context)
        return True
    
    def export_active_prod_images(self, cr, uid,ids,context=None):
        shop_obj=self.pool.get('magento.shop')
        shop_id = shop_obj.search(cr,uid,[('magento_shop','=',True)])[0]
        shop_obj.export_images(cr, uid,[shop_id],context)
        return True

    def export_multiple_products(self, cr, uid,ids,context=None):
        pro_obj = self.pool.get('product.product')
        active = pro_obj.browse(cr, uid, context.get(('active_ids'), []), context=context)
        for id in active:
            pro_obj.export_single_product(cr, uid,id,context)
        return True
    
export_active_products()
