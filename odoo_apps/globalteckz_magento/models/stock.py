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
# from PyMagento import Magento
import logging
logger = logging.getLogger('stock')


class stock_inventory(models.Model):
    _name = "stock.inventory"
    _inherit = "stock.inventory"

    
    magento_shop = fields.Many2one('magento.shop','Shop')
 

stock_inventory()

class Picking(models.Model):
    _inherit = 'stock.picking'

    magento_shop = fields.Many2one('magento.shop','Shop')
    is_magento = fields.Boolean(string='Magento')
    delivery_type = fields.Selection([
                ('odoo', 'Odoo'),
                ('magento', 'Magento'),
            ], 'Shipping Method')
#    shipping = fields.Char('Shipping')

    
    @api.model
    def create(self, vals):
        sale_obj = self.env['sale.order']
        stock = super(Picking, self).create(vals)
        sale_id = sale_obj.search([('name','=',stock.origin),('magento_order','=',True)])
        if sale_id:
            stock.write({'is_magento':True, 'magento_shop':sale_id.store_id.id})
        return stock

#     def do_partial(self,cr,uid,picking_ids, partial_data, context={}):
#         sale_obj=self.pool.get('sale.order')
#         shop_obj=self.pool.get('magento.shop')
#         prod_obj=self.pool.get('product.product')
#         pur_obj=self.pool.get('purchase.order')
#         res = super(stock_picking, self).do_partial(cr,uid,picking_ids, partial_data, context)
#         (data,)=self.browse(cr,uid,picking_ids)
# 
#         if data.type=='out':
#             if not data.origin:
#                 return res
#             sale_ids = sale_obj.search(cr,uid,[('name','=',data.origin)])
#             logger.error('sale_ids %s', sale_ids)
#             if not len(sale_ids):
#                 return res
#             sale_data = sale_obj.browse(cr,uid,sale_ids[0])
#             shop_data = sale_data.warehouse_id
#             if not shop_data.export_stock_del:
#                 return res
#         elif data.type=='in':
#             shop_ids=shop_obj.search(cr,uid,[('company_id','=',data.company_id.id)])
#             for shop_search_data in shop_obj.browse(cr,uid,shop_ids):
#                 if shop_search_data.magento_instance_id:
#                     shop_data = shop_search_data
#                     if not shop_data.export_stock_inv:
#                         return res
#                     break
#         else:
#             return res
# 
#         mage = Magento(shop_data.magento_instance_id.location,shop_data.magento_instance_id.apiusername,shop_data.magento_instance_id.apipassoword)
#         mage.connect()
# 
#         for partial_data_each in partial_data:
#             logger.error('partial_data_each %s', partial_data_each)
#             if partial_data_each.find('move') != -1:
#                 prod_data = prod_obj.browse(cr, uid, partial_data[partial_data_each]['product_id'])
#                 in_stock = 0
#                 if int(prod_data.qty_available) >= 1:
#                     in_stock = 1
#                 try:
#                     sku_list = {'qty':prod_data.qty_available,'is_in_stock':in_stock}
#                     logger.error('sku_list %s', sku_list)
#                     update=mage.client.service.catalogInventoryStockItemUpdate(mage.token,prod_data.default_code,sku_list)
#                 except:
#                     pass
# 
#         return res



# class stock_move(models.Model):
#     _inherit = "stock.move"
# 
# 
#     def _prepare_picking_assign(self, cr, uid, move, context=None):
#         """ Prepares a new picking for this move as it could not be assigned to
#         another picking. This method is designed to be inherited.
#         """
#         values = {
#             'origin': move.origin,
#             'company_id': move.company_id and move.company_id.id or False,
#             'move_type': move.group_id and move.group_id.move_type or 'direct',
#             'partner_id': move.partner_id.id or False,
#             'picking_type_id': move.picking_type_id and move.picking_type_id.id or False,
#             'location_id': move.location_id.id,
#             'location_dest_id': move.location_dest_id.id,
#         }
#         if move.procurement_id.sale_line_id:
#             order_id = move.procurement_id.sale_line_id.order_id
#             if not order_id.mage_order_id:
#                 values.update({
#                     'delivery_type' : 'odoo',
#                 })
#             else:
#                 values.update({
#                     'delivery_type' : 'magento',
#                 })
#         return values
# 
# stock_move()
