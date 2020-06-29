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
from . PyMagento import Magento
from datetime import datetime,date, timedelta
import time
import datetime
from odoo import netsvc
from suds.client import Client
import socket
from odoo.tools .translate import _
# import cStringIO  # *much* faster than StringIO
# import urllib
import urllib.request as urllib
from PIL import Image
import imghdr
import os
# from urllib import urlencode
from base64 import b64encode
# import base64
import logging
logger = logging.getLogger('sale')
from odoo.exceptions import UserError


ORDER_STATUS_MAPPING = {
'draft' : 'pending',
'sale_to_invoice': 'processing',
'done': 'complete',
'cancel': 'canceled',
}

class payment_method_magento(models.Model):
    _name = "payment.method.magento"
    
    name = fields.Char('Name')
    code = fields.Char('code')
    
payment_method_magento()


class sale_order(models.Model):
    _name = "sale.order"
    _inherit = "sale.order"
    
    mage_order_id = fields.Char('Order ID', size=100)
    payment_method = fields.Many2one('payment.method.magento', 'Payment Method')
    shipped = fields.Boolean('Shipped')
    invoiced = fields.Boolean('Invoiced')
    icon = fields.Binary('Icon')
    amazon_order_id = fields.Char('Amazon Order No')
    magento_order_id = fields.Char('Amazon Order No')
    created_date = fields.Date('Created Date')
    invoice_quantity = fields.Char('Invoice Qty')
    updated_date = fields.Date('Update Date')
    magento_status = fields.Char('Magento Order Status')
    magento_order = fields.Boolean('Magento Order')
    store_id = fields.Many2one('magento.shop', string='Magento Shop')
    sin_export_invoice = fields.Boolean(string="Export Invoice")
    sin_export_shipment = fields.Boolean(string="Export Shipment")
    
    
    
    _defaults = {
        'order_policy': 'picking',
        
    }

    @api.multi
    def single_export_shipment(self):
        stock_obj = self.env['stock.picking']
        invoice_obj = self.env['account.invoice']
        sale_obj = self.env['sale.order']
        magento_log = self.env['magento.log']
        magento_log_line = self.env['magento.log.details']
        log_id = magento_log.create({'create_date':date.today(), 'name': 'Single Export Shipment', 'description': 'Successfull'})
        shop_data = self
        try:
            mage = Magento(shop_data.store_id.magento_instance_id.location, shop_data.store_id.magento_instance_id.apiusername, shop_data.store_id.magento_instance_id.apipassoword)
            mage.connect()
            data = []
    #             try:
            print("shop_data.magento_status=",shop_data.magento_status)
            if (shop_data.magento_status == 'processing'or shop_data.magento_status == 'pending')  and shop_data.shipped == False:
                delivery_id = shop_data.picking_ids[0]
                print("delivery_id", delivery_id)
                if delivery_id.state == 'done':
                    shipmentIncrementId = shop_data.mage_order_id
                    if not shipmentIncrementId or not delivery_id.carrier_tracking_ref or not delivery_id.carrier_id.magento_code:
                        raise UserError(_('Error'), _('Please Enter Tracking Ref and Carrier'))
                    else:
                        for stock_data in delivery_id.move_lines:
                            prod_magento_id = stock_data.product_id.magento_id
                            prod_qty = stock_data.product_uom_qty
                            data += [prod_magento_id, prod_qty]
                        shiping_id = mage.client.service.salesOrderShipmentCreate(mage.token, shipmentIncrementId, data)
                        logger.error('shiping_id %s', shiping_id)
                        self.write({'shipped':True, 'sin_export_shipment':True})
        
                    if not shiping_id in ['102', '103', '100']:
                        if not delivery_id.carrier_id or not delivery_id.carrier_id.magento_code:
                            raise  UserError(_('Error'), _('Please Enter Carrier Delivery'))
                        else:
                            carrier = delivery_id.carrier_id.magento_code
                            print("carrier", carrier)
                            title = delivery_id.carrier_id.name
                            trackNumber = delivery_id.carrier_tracking_ref
                            logger.error('trackNumber %s', trackNumber)
                            track = mage.client.service.salesOrderShipmentAddTrack(mage.token, shiping_id, carrier, title, trackNumber)
                            logger.error('track %s', track)
                                
                    
                else:
                    raise UserError(_('Error'), _('Please confirm your delivery to be done'))
            else:
                raise UserError(_('Error'), _('Please check your order this may have already shipped'))
        
        except Exception as exc:
            logger.error('Exception===================:  %s', exc)
            magento_log_line.create({'name':'Single Export Shipment', 'description':exc, 'create_date':date.today(),
                                      'magento_log_id':log_id.id})
            log_id.write({'description': 'Something went wrong'}) 
            pass
        return True
    
    @api.multi
    def single_export_invoice(self):
        invoice_obj = self.env['account.invoice']
        magento_log = self.env['magento.log']
        magento_log_line = self.env['magento.log.details']
        log_id = magento_log.create({'create_date':date.today(), 'name': 'Single Export Invoice', 'description': 'Successfull'})
        shop_data = self
        mage = Magento(shop_data.store_id.magento_instance_id.location, shop_data.store_id.magento_instance_id.apiusername, shop_data.store_id.magento_instance_id.apipassoword)
        mage.connect()
        data = []
        try:
            if (shop_data.magento_status == 'pending' or shop_data.magento_status == 'processing') and shop_data.invoiced == False:
                invoice_id = shop_data.invoice_ids[0]
                itemsQty = {}
                for line in shop_data.order_line:
                    print (line.product_id)
                    item_qty = line.product_uom_qty
                    order_item_qty = line.product_id.magento_id
                    itemsQty = {'order_item_id' :order_item_qty , 'qty' : item_qty }
                    data += [order_item_qty, item_qty]
                    shipmentIncrementId = shop_data.mage_order_id
                if invoice_id.state == 'paid':
                    inv_id = mage.client.service.salesOrderInvoiceCreate(mage.token, shipmentIncrementId, data)
                    print ('invv_id++++++++++++++++++' , inv_id)
                    self.write({'magento_status':'complete', 'invoiced': True, 'sin_export_invoice':True})
                else:
                    raise UserError(_('Error'), _('Please confirm your invoice to be paid'))
            else:
                raise UserError(_('Error'), _('Please check your order this may have already invoiced'))
        except Exception as exc:
            logger.error('Exception===================:  %s', exc)
            magento_log_line.create({'name':'Single Export Invoice', 'description':exc, 'create_date':date.today(),
                                      'magento_log_id':log_id.id})
            log_id.write({'description': 'Something went wrong'}) 
            pass
        return True

    # @api.multi
    # def action_confirm(self):
    #     inventory_obj = self.env['stock.picking']
    #     for order in self:
    #         order.state = 'sale'
    #         order.confirmation_date = fields.Datetime.now()
    #         if self.env.context.get('send_email'):
    #             self.force_quotation_send()
    #         order.order_line._action_procurement_create()
    #         #_action_launch_procurement_rule
    #     if self.env['ir.values'].get_default('sale.config.settings', 'auto_done_setting'):
    #         self.action_done()
    #     return True
#
#
class magento_shop(models.Model):
    _name = "magento.shop"

    name = fields.Char('Store / Warehouse Name')
    code = fields.Char('Short Name', size=5, help="Short name used to identify your warehouse")
    magento_instance_id = fields.Many2one('magento.instance', 'Instance', readonly=True)
    magento_shop = fields.Boolean('Magento Shop', readonly=True)
    last_mag_update_order_date = fields.Datetime('Last Order Update Time')
    prefix = fields.Char('Prefix', size=64 , default='mag_', readonly=True)
    magento_code = fields.Char('Code', size=64)
    store_id = fields.Integer('Store ID', readonly=True)
    website_id = fields.Integer('Website ID', readonly=True)
    start_date = fields.Datetime('Start Update Status Date')
    order_place = fields.Date('Date of Import Stock')
    last_update_cust = fields.Date('Date of Last Update Customer')
    last_update_cust_grp = fields.Date('Date of Last Update Customer Group')
    export_stock_date = fields.Date('Date of Export Stock')
    magento_shop = fields.Boolean('Magento Shop', readonly=True)
    export_stock_del = fields.Boolean('Export Stock On Delivery Orders')
    export_stock_inv = fields.Boolean('Export Stock On Incoming Shipment')
    price_include = fields.Boolean('Cost Price Include Taxes')
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')
    workflow_id = fields.Many2one('import.order.workflow', string='Worflow Configuration')

   
    @api.one
    def export_products(self):
        image_obj = self.env['product.images']
        prod_obj = self.env['product.product']
        product_id = prod_obj.search([('magento_exported', '=', True), ('select_instance', '=', self.magento_instance_id.id)])
        for prod_data in product_id:
            if not prod_data.select_instance:
                raise  UserError(_('Error'), _('Please Select Magento Instance'))
            (shop_data,) = prod_data.select_instance
            mage = Magento(shop_data.location, shop_data.apiusername, shop_data.apipassoword)
            mage.connect()
            attribute = mage.client.factory.create('catalogProductReturnEntity')
            product_Data = {}
            if not prod_data.default_code:
                raise  UserError(_('Error'), _('Please Enter SKU'))
            if not prod_data.attribute_id:
                raise  UserError(_('Error'), _('Please Enter Attribute SET'))
            attribute = mage.client.factory.create('catalogProductAdditionalAttributesEntity')
            print( "AAAAAAAAAAA", attribute)
            attributes = []
            for atts in prod_data.magento_attribute:
                if atts.market_pl.attribute_code == 'name':
                    continue
                if atts.market_pl.attribute_code == 'description':
                    continue
                if atts.market_pl.attribute_code == 'short_dexcription':
                    continue
                if atts.market_pl.attribute_code == 'price':
                    continue
                if atts.market_pl.attribute_code == 'meta_title':
                    continue
                if atts.market_pl.attribute_code == 'meta_keyword':
                    continue
                if atts.market_pl.attribute_code == 'meta_description':
                    continue
                attributes.append({'key': atts.market_pl.attribute_code, 'value': atts.market_ch.value })
            if attributes:
                print ("ATRRRRRRRRRRRRIBUTESSSSSSSSSSSSSSS", attributes)
                attribute['single_data'] = [attributes]
            sku = prod_data.default_code
            type = prod_data.product_type or 'simple'
            set = prod_data.attribute_id.code
            id = prod_data.magento_id
            websites_list = []
            if len(prod_data.shop_prod_ids):
                for each_shop in prod_data.shop_prod_ids:
                    if each_shop.store_id:
                        websites_list.append(str(each_shop.store_id))
            if prod_data.special_price and prod_data.special_price_from_date and prod_data.special_price_to_date:
                product_Data = {
                    'name':prod_data.name,
                    'description':prod_data.mag_description or '',
                    'short_description':prod_data.mag_short_description or '',
                    'price':prod_data.lst_price,
                    'categories':[str(prod_data.categ_id.magento_id)],
                    'status': 1,
                    'weight':prod_data.weight,
                    'visibility':prod_data.visibility or 4,
                    'meta_title':prod_data.meta_title[:225] if prod_data.meta_title else '',
                    'meta_keyword':prod_data.meta_keyword[:225] if prod_data.meta_keyword else '',
                    'meta_description':prod_data.meta_description[:225] if prod_data.meta_description else '',
                    'special_price':prod_data.special_price or 0.0,
                    'special_from_date':prod_data.special_price_from_date or False,
                    'special_to_date':prod_data.special_price_to_date or False,
                    'tax_class_id' : prod_data.tax_class or '',
                    'websites' : websites_list,
                    'additional_attributes':attribute
                }
                print("--prduct date", product_Data)
            else:
                product_Data = {
                    'name':prod_data.name,
                    'description':prod_data.mag_description or '',
                    'short_description':prod_data.mag_short_description or '',
                    'price':prod_data.lst_price,
                    'categories':[str(prod_data.categ_id.magento_id)],
                    'status':prod_data.status_type or 1,
                    'weight':prod_data.weight,
                    'visibility':prod_data.visibility or 4,
                    'meta_title':prod_data.meta_title[:225] if prod_data.meta_title else '',
                    'meta_keyword':prod_data.meta_keyword[:225] if prod_data.meta_keyword else '',
                    'meta_description':prod_data.meta_description[:225] if prod_data.meta_description else '',
                    'websites' : websites_list,
                    'tax_class_id' : prod_data.tax_class or '',
                    'additional_attributes':attribute
                }
                print("--prduct date 1111", product_Data)
            if len(prod_data.prods_cat_id):
                product_Data['categories'] = []
                for each_categ in prod_data.prods_cat_id:
                    print("each_categ", each_categ)
                    if each_categ.name.magento_id:
                        product_Data['categories'].append(each_categ.name.magento_id)
                        print ("product_Data['categories']", product_Data['categories'])
            try:
                if not prod_data.magento_exported:
                    list_prods = mage.client.service.catalogProductCreate(mage.token, type, set, sku, product_Data)
                    prod_data.write({'magento_exported':True, 'magento_id':list_prods})
                else:
                    list_prods = mage.client.service.catalogProductUpdate(mage.token, prod_data.magento_id, product_Data, 0, 'ID')
                    logger.error('---------simple----------list_prods %s', list_prods)
            except Exception as exc:
                logger.error('exc %s', exc)
                prod_data.write({'is_faulty':True, 'faulty_log':str(exc)})
                self._cr.commit()
        return True


    @api.multi
    def export_link_products(self):
#       Update Related Products, Up-sell Products, Cross-sell Products To Magento Products
        magento_log = self.env['magento.log']
        magento_log_line = self.env['magento.log.details']
        log_id = magento_log.create({'create_date':date.today(), 'name': 'Export Link Product', 'description': 'Successfull'})
        related_prod_skus = []
        upsell_prod_skus = []
        cross_sells_prod_skus = []
        prod_obj = self.env['product.product']
        (shop_data,) = self
        try:
            product_id = prod_obj.search([('type', '!=', 'service'), ('active', '=', True), ('magento_exported', '=', True), ('select_instance', '=', shop_data.magento_instance_id.id), ('magento_id', '!=', '')])
            mage = Magento(shop_data.magento_instance_id.location, shop_data.magento_instance_id.apiusername, shop_data.magento_instance_id.apipassoword)
            mage.connect()
            for prod_data in product_id:
                try:
                    if prod_data.magento_exported:
                        if not prod_data.default_code:
                            # raise osv.except_osv(_('Error'), _('Please Enter SKU for %s' % (prod_data.name)))
                            raise UserError(_('Please Enter SKU for %s') % \
                                    (prod_data.name))
                        if not prod_data.attribute_id:
                            # raise osv.except_osv(_('Error'), _('Please Enter Attribute SET for %s' % (prod_data.name)))
                            raise UserError(_('Please Enter Attribute SET for %s') % \
                                    (prod_data.name))
                        sku = prod_data.default_code
                        set = prod_data.attribute_id.code

                        if prod_data.related_prod_ids:
                            for related_prod_id in prod_data.related_prod_ids:
                                if related_prod_id.default_code:
                                    if related_prod_id.magento_exported:
                                        data = { 'position':0, 'qty':1 }
                                        related_prod_sku = related_prod_id.default_code
                                        list_prods = mage.client.service.catalogProductLinkAssign(mage.token, 'related', sku, related_prod_sku, data, 'sku')
                                    else:
                                        # raise osv.except_osv(_('Error'), _('Related SKU %s not in Magento' % (related_prod_id.default_code)))
                                        raise UserError(_('Related SKU %s not in Magento') % \
                                        (related_prod_id.default_code))
                        if prod_data.upsell_prod_ids:
                            for upsell_prod_id in prod_data.upsell_prod_ids:
                                if upsell_prod_id.default_code:
                                    if upsell_prod_id.magento_exported:
                                        data = { 'position':0, 'qty':1 }
                                        upsell_prod_sku = upsell_prod_id.default_code
                                        list_prods = mage.client.service.catalogProductLinkAssign(mage.token, 'up_sell', sku, upsell_prod_sku, data, 'sku')
                                    else:
                                        # raise osv.except_osv(_('Error'), _('Upsell SKU %s not in Magento' % (upsell_prod_id.default_code)))
                                        raise UserError(_('Related SKU %s not in Magento') % \
                                        (upsell_prod_id.default_code))
                        if prod_data.cross_sells_prod_ids:
                            for cross_sells_prod_id in prod_data.cross_sells_prod_ids:
                                if cross_sells_prod_id.default_code:
                                    if cross_sells_prod_id.magento_exported:
                                        data = { 'position':0, 'qty':1 }
                                        cross_sells_prod_sku = cross_sells_prod_id.default_code
                                        list_prods = mage.client.service.catalogProductLinkAssign(mage.token, 'cross_sell', sku, cross_sells_prod_sku, data, 'sku')
                                    else:
                                        # raise osv.except_osv(_('Error'), _('Cross sell SKU %s not in Magento' % (cross_sells_prod_id.default_code)))
                                        raise UserError(_('Related SKU %s not in Magento') % \
                                        (cross_sells_prod_id.default_code))
                except Exception as exc:
                    logger.error('Exception===================:  %s', exc)
                    magento_log_line.create({'name':'Export Link Product', 'description':exc, 'create_date':date.today(),
                                              'magento_log_id':log_id.id})
                    log_id.write({'description': 'Something went wrong'}) 
                    pass 
        except Exception as exc:
            logger.error('Exception===================:  %s', exc)
            log_id.write({'description': exc})
            pass
        return True


    @api.multi
    def export_new_products(self):
        print(" getting call ")
        #        sNotimplemented
        prod_obj = self.env['product.product']
        magento_log = self.env['magento.log']
        magento_log_line = self.env['magento.log.details']
        log_id = magento_log.create({'create_date':date.today(), 'name': 'Export New Product', 'description': 'Successfull'})
        print(" log_id====", log_id)
        (shop_data,) = self
        try:
            product_id = prod_obj.search([('type', '!=', 'service'), ('magento_exported', '=', False), ('select_instance', '=', shop_data.magento_instance_id.id)])
            print("product_id==", product_id)
            mage = Magento(shop_data.magento_instance_id.location, shop_data.magento_instance_id.apiusername, shop_data.magento_instance_id.apipassoword)
            print("mage===", mage)
            mage.connect()
            for prod_data in product_id:
                try:
                    print ('export new product')
                    if not prod_data.magento_exported:
                        print ('export new product')
                        product_Data = {}
                        if not prod_data.default_code:
                            # raise osv.except_osv(_('Error'), _('Please Enter SKU for %s' % (prod_data.name)))
                            raise UserError(_('Please Enter SKU for %s') % \
                                    (prod_data.name))
                        if not prod_data.attribute_id:
                            # raise osv.except_osv(_('Error'), _('Please Enter Attribute SET for %s' % (prod_data.name)))
                            raise UserError(_('Please Enter Attribute SET for %s') % (prod_data.name))
                        attribute = mage.client.factory.create('catalogProductAdditionalAttributesEntity')
                        print ("AAAAAAAAAAA", attribute)
                        attributes = []
                        for atts in prod_data.magento_attribute:
                            if atts.market_pl.attribute_code == 'name':
                                continue
                            if atts.market_pl.attribute_code == 'description':
                                continue
                            if atts.market_pl.attribute_code == 'short_dexcription':
                                continue
                            if atts.market_pl.attribute_code == 'price':
                                continue
                            if atts.market_pl.attribute_code == 'meta_title':
                                continue
                            if atts.market_pl.attribute_code == 'meta_keyword':
                                continue
                            if atts.market_pl.attribute_code == 'meta_description':
                                continue
                            attributes.append({'key': atts.market_pl.attribute_code, 'value': atts.market_ch.value })
                        if attributes:
                            attribute['single_data'] = [attributes]
                        sku = prod_data.default_code
                        type = prod_data.product_type or 'simple'
                        set = prod_data.attribute_id.code
                        websites_list = []
                        
                        product_Data = {
                            'name':prod_data.name,
                            'description':prod_data.mag_description or '',
                            'short_description':prod_data.mag_short_description or '',
                            'price':prod_data.lst_price,
                            'categories':[str(prod_data.categ_id.magento_id)],
                            'status':prod_data.status_type or 1,
                            'weight':prod_data.weight,
                            'visibility':prod_data.visibility or 4,
                            'meta_title':prod_data.meta_title[:225] if prod_data.meta_title else '',
                            'meta_keyword':prod_data.meta_keyword[:225] if prod_data.meta_keyword else '',
                            'meta_description':prod_data.meta_description[:225] if prod_data.meta_description else '',
                            'special_price':prod_data.special_price or 0.0,
                            'special_from_date':prod_data.special_price_from_date or False,
                            'special_to_date':prod_data.special_price_to_date or False,
                            'tax_class_id' : prod_data.tax_class or '',
                            'websites' : websites_list,
                            'additional_attributes':attribute,
                        }
        
                        # Update multiple Categories to Magento
                        if len(prod_data.prods_cat_id):
                            product_Data['categories'] = []
                            for each_categ in prod_data.prods_cat_id:
                                if each_categ.name.magento_id:
                                    product_Data['categories'].append(each_categ.name.magento_id)
                            list_prods = mage.client.service.catalogProductCreate(mage.token, type, set, sku, product_Data)
                            prod_data.write({'magento_exported':True, 'magento_id':list_prods})
                except Exception as exc:
                    logger.error('Exception===================:  %s', exc)
                    magento_log_line.create({'name':'Export New Product', 'description':exc, 'create_date':date.today(),
                                               'magento_log_id':log_id.id})
                    log_id.write({'description': 'Something went wrong'}) 
                    pass 
        except Exception as exc:
            logger.error('Exception===================:  %s', exc)
            log_id.write({'description': exc})
            pass
        return True
    
    @api.one
    def export_images(self):
        prod_obj = self.env['product.product']
        image_obj = self.env['product.images']
        magento_log = self.env['magento.log']
        magento_log_line = self.env['magento.log.details']
        log_id = magento_log.create({'create_date':date.today(), 'name': 'Export Image', 'description': 'Successfull'})
        (shop_data,) = self
        try:
            product_id = prod_obj.search([('type', '!=', 'service'), ('select_instance', '=', shop_data.magento_instance_id.id), ('magento_id', '!=', '')])
            print("product_id",product_id)
            mage = Magento(shop_data.magento_instance_id.location, shop_data.magento_instance_id.apiusername, shop_data.magento_instance_id.apipassoword)
            mage.connect()
            data = {}
            datar = []
            for prod_data in product_id:
                print("prod_data",prod_data)
                image_id = image_obj.search([('product_id', '=', prod_data.id)])
                print("image_id",image_id)
                for image_data in image_id:
                    try:
                        if not image_data.is_exported:
                            if image_data.link == True:
                                file_contain = urllib.urlopen(image_data.url).read()
                                image_path = b64encode(file_contain)
                                image_path = image_path.decode('utf-8')

                                #                        type = imghdr.what(str(image_data.url))
                                image = 'image/jpeg'
                            else:
                                image_path = image_data.file_db_store
                                image = 'image/jpeg'
                            file = {
                                'content':image_path,
                                'mime':image,
                                'name':image_data.name,
                            }

                            image_type = []
                            if image_data.image:
                                image_type.append('image')
                            if image_data.small_image:
                                image_type.append('small_image')
                            if image_data.thumbnail:
                                image_type.append('thumbnail')


                            data = {
                                'label': image_data.name,
                                'position':image_data.position,
                                'types':image_type,
                                'exclude':'0',
                                'file':file,
                                'remove':'0'
                            }
                            print("data",data)
                            mage.client.service.catalogProductAttributeMediaCreate(mage.token, prod_data.default_code, data, 0, 'sku')
                            image_data.write({'is_exported':True})
                    except Exception as exc:
                        logger.error('Exception===================:  %s', exc)
                        magento_log_line.create({'name':'Export Image', 'description':exc, 'create_date':date.today(),
                                                  'magento_log_id':log_id.id})
                        log_id.write({'description': 'Something went wrong'}) 
                        pass
        except Exception as exc:
            logger.error('Exception===================:  %s', exc)
            log_id.write({'description': exc})
            pass
        return True
    
#
#    def _sale_shop(self, cr, uid, callback, context=None):
#        if context is None:
#            context = {}
#        proxy = self.pool.get('magento.shop')
#        domain = [ ('magento_shop', '=', True)]
#        ids = proxy.search(cr, uid, domain, context=context)
#        if ids:
#            callback(cr, uid, ids, context=context)
#
#        return True
#    
#    def _sale_shop_1(self, cr, uid, callback, context=None):
#        if context is None:
#            context = {}
#        proxy = self.pool.get('magento.shop')
#        domain = [ ('magento_shop', '=', True) ]
#        ids = proxy.search(cr, uid, domain, context=context)
#        if ids:
#            callback(cr, uid, ids[0], context=context)
#
#        return True
#    
#    def run_import_orders_scheduler(self, cr, uid, context=None):
#        self._sale_shop(cr, uid, self.import_orders, context=context)
#
#    def run_export_shipping_scheduler(self, cr, uid, context=None):
#        self._sale_shop(cr, uid, self.export_order_status, context=context)
#
#    def run_import_att_set_scheduler(self, cr, uid, context=None):
#        self._sale_shop(cr, uid, self.import_att_set, context=context)
#
#
#
#    
    @api.one
    def updatePartnerAddress(self, resultval, cust_grp, mage):
        resultvals = resultval.shipping_address
        street, city, phone, postalcode, state_id, country_id, email_new, mage_cust_id = '', '', '', '', False, \
            False, '', False
        if resultvals:
            if 'street' in resultvals:
                street = resultvals.street
            if 'city' in resultvals:
                city = resultvals.city
            if 'telephone' in resultvals:
                phone = resultvals.telephone

            if 'postcode' in resultvals:
                postalcode = resultvals.postcode
            if 'customer_email' in resultvals:
                email_new = resultvals.customer_email
#            if 'country_id' in resultvals:
#                country_id = resultvals.country_id
        state_id = False
        country_id = False
        if hasattr(resultvals , 'country_id'):
            country_id = self.env['res.country'].search(['|',('code', '=ilike', (resultvals.country_id)),('code', '=ilike',resultvals.country_id[:2])])
            if not country_id:
                country_id = self.env['res.country'].create({'code':resultvals['country_id'][:2], 'name':resultvals['country_id']})
            else:
                country_id = country_id[0]
            if country_id:
                if hasattr(resultvals , 'region'):
                    state_ids = self.env['res.country.state'].search(['|',('code','=ilike',resultvals.region),('name', '=ilike', resultvals.region),('country_id','=',country_id.id)])
                    if state_ids:
                        state_id = state_ids[0].id
                    if not state_ids:
                        state_ids = self.env['res.country.state'].search(['|', ('code', '=ilike', resultvals.region[:3]),('country_id', '=', country_id.id)])
                        print("state_ids",state_ids)
                        if state_ids:
                            state_id = state_ids[0].id

                        else:
                            state_id = self.env['res.country.state'].create({'country_id':country_id[0].id, 'name':resultvals.region, 'code':resultvals['region'][:3]}).id
                            print("state_id",state_id)
                    # else:
                #     state_id = state_ids[0].id
        
            name = False
            if hasattr(resultvals , 'firstname') and hasattr(resultvals , 'lastname'):
                name = resultvals.firstname + ' ' + resultvals.lastname
            elif hasattr(resultvals , 'firstname'):
                name = resultvals.firstname
            elif hasattr(resultvals , 'lastname'):
                name = resultvals.lastname

            contact_name = False
            if hasattr(resultvals , 'company'):
                contact_name = name.strip(' ')
                name = resultvals.company
        addressvals = {
            'name' : name.strip(' '),
            'contact_name' : contact_name,
            'street' : street,
            'city' : city,
#            'customer_grp':cust_grp.id,
#            'street2' : street2,
            'country_id' : country_id.id,
            'phone' : phone,
            'zip' : postalcode,
            'state_id' : state_id,
            'email' : email_new,
            'mage_cust_id' : self.id,
        }
        print("addressvals",addressvals)
        partner_address_ids = self.env['res.partner'].search([('email', '=', email_new)])
        if len(partner_address_ids):
            data = partner_address_ids.write(addressvals)
            address_id = partner_address_ids[0]
        else:
            address_id = self.env['res.partner'].create(addressvals)
        return address_id
    
    
    @api.one
    def updateBillingAddress(self, resultvals, cust_grp, mage):
        street, city, phone, postcode, state_id, country_id, email_new, mage_cust_id = '', '', '', '', False, \
            False, '', False
        bill = resultvals.billing_address
        ship = resultvals.shipping_address
        bill_address_id = False

        bill_postcode = False
        ship_postcode = False

        ship_street = False
        bill_street = False

        ship_country_id = False
        bill_country_id = False
        bill_region = False

        if hasattr(resultvals.billing_address , 'country_id'):
            bill_country_id = bill.country_id

        if hasattr(resultvals.billing_address , 'region'):
            bill_region = bill.region

        if hasattr(resultvals.shipping_address , 'country_id'):
            ship_country_id = ship.country_id

        if hasattr(resultvals.billing_address , 'postcode'):
            bill_postcode = bill.postcode

        if hasattr(resultvals.shipping_address , 'postcode'):
            ship_postcode = ship.postcode

        if hasattr(resultvals.billing_address , 'street'):
            bill_street = bill.street
            
        if hasattr(resultvals.shipping_address , 'street'):
            ship_street = ship.street
        if  bill_country_id != ship_country_id or bill_street != ship_street or ship_postcode != bill_postcode:
            if 'country_id' in bill:
                country_id = self.env['res.country'].search(['|', ('code', '=ilike', bill_country_id), ('code', '=ilike', bill_country_id[:2])])
                if not country_id:
                    country_id = self.env['res.country'].create({'code':bill_country_id[:2], 'name': bill_country_id})
                else:
                    country_id = country_id[0]
                if country_id:
                    if 'region' in bill:
                        state_ids = self.env['res.country.state'].search(['|', ('code', '=ilike', bill_region), ('name', '=ilike', bill_region), ('country_id', '=', country_id.id)])
                        if state_ids:
                            state_id = state_ids[0].id
                        if not state_ids:
                            state_ids = self.env['res.country.state'].search(['|', ('code', '=ilike', bill_region[:3]), ('country_id', '=', country_id.id)])
                            print("state_ids", state_ids)
                            if state_ids:
                                state_id = state_ids[0].id

                            else:
                                state_id = self.env['res.country.state'].create({'country_id': country_id.id, 'name': bill_region,'code': bill_region[:3]}).id
                                print("state_id", state_id)

        # #             state_id = ''
        # #             if hasattr(resultvals.billing_address , 'region'):
        # #                 state_ids = self.env['res.country.state'].search([('name', '=', bill.region)])
        # #                 state_ids = self.env['res.country.state'].search( ['|', ('code', '=ilike', bill.region), ('name', '=ilike', bill.region),
        # #                      ('country_id', '=', country_id.id)])
        # #                 if state_ids:
        # #                     state_id = state_ids[0].id
        # # #                if not state_ids:
        # # #                    state_id = self.pool.get('res.country.state').create(cr,uid,{'country_id':country_id, 'name':bill.region, 'code':bill['region'][:3]})
        # # #                else:
        # #                 if state_ids:
        # #                     state_id = state_ids[0].id
        # #                 if not state_ids:
        #                     state_id = False

            street = False
            if hasattr(bill , 'street'):
                street = bill.street

            city = False
            if hasattr(bill , 'city'):
                city = bill.city

            postalcode = False
            if hasattr(bill , 'postcode'):
                postalcode = bill.postcode

            phone = False
            if hasattr(bill , 'telephone'):
                phone = bill.telephone

            email_new = False
            if resultvals.customer_email:
                email_new = resultvals.customer_email

            name = False
            if hasattr(bill , 'firstname') and hasattr(bill , 'lastname'):
                name = bill.firstname + ' ' + bill.lastname
            elif hasattr(bill , 'firstname'):
                name = bill.firstname
            elif hasattr(bill , 'lastname'):
                name = bill.lastname
            contact_name = False
            if hasattr(resultvals , 'company'):
               contact_name = name.strip(' ')
               name = resultvals.company
               
            addressvals = {
                'name' : name.strip(' '),
                'contact_name' : contact_name,
                'street' : street,
                'city' : city,
    #            'street2' : street2,
                'country_id' : country_id.id,
                'customer_grp':cust_grp,
                'phone' : phone,
                'zip' : postalcode,
                'state_id' : state_id,
                'email' : email_new,
                'mage_cust_id' : self[0].id,
            }   
            partner_address_ids = self.env['res.partner'].search([('email', '=', email_new)])
            if len(partner_address_ids):
                data1 = partner_address_ids.write(addressvals)
                bill_address_id = partner_address_ids[0]
            else:
                bill_address_id = self.env['res.partner'].create(addressvals)
        return bill_address_id

    @api.one
    def import_orders(self):
        customer_obj = self.env['customer.group']
        delivery_obj = self.env['delivery.carrier']
        saleorder_obj = self.env['sale.order']
        magento_log = self.env['magento.log']
        magento_log_line = self.env['magento.log.details']
        log_id = magento_log.create({'create_date':date.today(), 'name': 'Import Orders', 'description': 'Successfull'})
        for shop_data in self:
#             try:
            if not shop_data.last_mag_update_order_date:
                raise  UserError(_('Error'), _('Please Select Date for Order Import'))
            DD = datetime.timedelta(days=1)
            import_Date = str(shop_data.last_mag_update_order_date)
            print("import_Date",import_Date)
            date_time = datetime.datetime.strptime(import_Date, '%Y-%m-%d %H:%M:%S').date()
            new_import_date = str(date_time - DD)
            print ('new_import_date', new_import_date)
            logger.error('new_import_date %s', new_import_date)
            value_date = {'key':'gteq', 'value':new_import_date}
#                 order_status = ['processing', 'pending', 'complete']
            order_status = ['complete']
            state = {'key':'in', 'value':order_status}
            store_id = {'key':'eq', 'value':shop_data.store_id}
            print("store_id",store_id)
            params = [{'complex_filter':[{'key':'updated_at', 'value':value_date}, {'key':'store_id', 'value':store_id}]}]
            print("params",params)
            mage = Magento(shop_data.magento_instance_id.location, shop_data.magento_instance_id.apiusername, shop_data.magento_instance_id.apipassoword)
            mage.connect()
            order_lists = mage.client.service.salesOrderList(mage.token, params)
            print("order_lists", len(order_lists))
            for orderinfo in order_lists:
                print("orderinfo['increment_id'", orderinfo['increment_id'])
                cust_grp = False
                cust_grp_id = customer_obj.search([('customer_group_code', '=', orderinfo['customer_group_id'])])
                if cust_grp_id:
                    cust_grp = cust_grp_id[0].id

                if hasattr(orderinfo , 'increment_id'):
                    logger.error('increment_id %s', orderinfo['increment_id'])
                    saleorderid = saleorder_obj.search([('mage_order_id', '=', orderinfo['increment_id'])])
                    if not saleorderid:
                        orders = mage.client.service.salesOrderInfo(mage.token, orderinfo['increment_id'])
                        print("orders", orders)
                        if hasattr(orders , 'shipping_description'):
                            # if orders.shipping_description:
                            #     delivery_id=self.create_delivery_method(orders)
                            # else:
                            #     delivery_id=self.create_delivery_method(orders)
                            partner_add = self.updatePartnerAddress(orders, cust_grp, mage)
                            billing_add = self.updateBillingAddress(orders, cust_grp, mage)
                            self.createOrder(orders, partner_add, billing_add, log_id)
#             except Exception as exc:
#                 logger.error('Exception===================:  %s', exc)
#                 log_id.write({'description': exc})
#                 pass
#                             
        today = date.today()
        update = shop_data.write({'last_mag_update_order_date':today})
        return True

    @api.multi
    def create_delivery_method(self,order):
        print("order====",order)

        delivery_obj=self.env['delivery.carrier']
        res_obj=self.env['res.partner']
        prod_obj=self.env['product.product']
        val={}
        res_ids=res_obj.search([('name','=',order.shipping_description)])
        if res_ids:
            partner_id=res_ids[0]
        else:
            partner_id=res_obj.create({'name':order.shipping_description})
        prod_idsd=prod_obj.search([('default_code','=','SHIP MAGENTO')])
        if prod_idsd:
            prod_ids = prod_idsd
        else:
            prod_ids = []
        val={
        'name':order.shipping_description or '',
        'magento_code':order.get('shipping_method'),
        'partner_id':partner_id.id,
        'product_id':prod_ids.id,
        }
        dev_ids=delivery_obj.search([('name','=',order.shipping_description)])
         
        if not dev_ids:
            delivery_id=delivery_obj.create(val)
        else:
            delivery_id=dev_ids[0]
        
        return delivery_id

    @api.one
    def import_orders_dashboard(self, dates):
        customer_obj = self.env['customer.group']
        delivery_obj = self.env['delivery.carrier']
        saleorder_obj = self.env['sale.order']
        magento_log = self.env['magento.log']
        magento_log_line = self.env['magento.log.details']
        log_id = magento_log.create({'create_date':date.today(), 'name': 'Import order Dashboard', 'description': 'Successfull'})
        for shop_data in self:
#             try:
                if not dates:
                    raise  UserError(_('Error'), _('Please Select Date for Order Import'))
                print("datesdatesdates",dates)
                DD = datetime.timedelta(days=1)
                date_time = datetime.datetime.strptime(str(dates), '%Y-%m-%d %H:%M:%S').date()
                new_import_date = str(date_time - DD)
                print ('new_import_date', new_import_date)
                logger.error('new_import_date %s', new_import_date)
                value_date = {'key':'gteq', 'value':new_import_date}
#                 order_status = ['processing', 'pending', 'complete']
                order_status = ['complete']
                state = {'key':'in', 'value':order_status}
                store_id = {'key':'eq', 'value':shop_data.store_id}
                params = [{'complex_filter':[{'key':'updated_at', 'value':value_date}, {'key':'store_id', 'value':store_id}]}]
                print("paramsparamsparams",params)
                mage = Magento(shop_data.magento_instance_id.location, shop_data.magento_instance_id.apiusername, shop_data.magento_instance_id.apipassoword)
                mage.connect()
                order_lists = mage.client.service.salesOrderList(mage.token, params)
                print("order_listsorder_listsorder_lists",order_lists)
                for orderinfo in order_lists:
                    print("orderinfoorderinfo>>>>>>>",orderinfo)
                    cust_grp = False
                    cust_grp_id = customer_obj.search([('customer_group_code', '=', orderinfo['customer_group_id'])])
                    if cust_grp_id:
                        cust_grp = cust_grp_id[0].id
                    if hasattr(orderinfo , 'increment_id'):
                        logger.error('increment_id %s', orderinfo['increment_id'])
                        saleorderid = saleorder_obj.search([('mage_order_id', '=', orderinfo['increment_id'])])
                        print("saleorderidsaleorderid",saleorderid)
                        if not saleorderid:
                            orders = mage.client.service.salesOrderInfo(mage.token, orderinfo['increment_id'])
                            print("ordersordersordersorders>>>>>",orders)
                            if hasattr(orders , 'shipping_description'):
                                # if orders.shipping_description:
                                #     delivery_id=self.create_delivery_method(orders)
                                # else:
                                #     delivery_id=self.create_delivery_method(orders)
                                partner_add = self.updatePartnerAddress(orders, cust_grp, mage)
                                billing_add = self.updateBillingAddress(orders, cust_grp, mage)
                                self.createOrder(orders, partner_add, billing_add, log_id)
                     
#             except Exception as exc:
#                 logger.error('Exception===================:  %s', exc)
#                 log_id.write({'description': exc})
#                 pass
#                             
        today = date.today()
        update = shop_data.write({'last_mag_update_order_date':today})
        return True
    
    
    
    @api.multi
    def create_delivery_method(self, order):
        print("order===",order)
        delivery_obj = self.env['delivery.carrier']
        res_obj = self.env['res.partner']
        prod_obj = self.env['product.product']
        val = {}
        res_ids = res_obj.search([('name', '=', order.shipping_description)])
        if res_ids:
            partner_id = res_ids[0]
        else:
            partner_id = res_obj.create({'name':order.shipping_description})

        prod_ids = prod_obj.search([('default_code', '=', 'SHIP MAGENTO')])
#         if prod_ids:
        prod_ids = prod_ids.id
#         else:
#             prod_ids = [] 
        val = {
            'name':order.shipping_description or '',
            'magento_code':order.get('shipping_method'),
            'partner_id':partner_id.id,
            'product_id':prod_ids,
        }
        dev_ids = delivery_obj.search([('name', '=', order.shipping_description)])
        if not dev_ids:
            delivery_id = delivery_obj.create(val)
        else:
            delivery_id = dev_ids[0]
        return delivery_id
    
    
    @api.one
    def createUpdateProduct(self, product_details,):
        prod_obj = self.env['product.product']
        item_price = 1.0
        if hasattr(product_details, 'base_price'):
            item_price = product_details['base_price']
        product_ids = prod_obj.search([('default_code', '=', product_details['sku']), ('active', '=', True)])
        if not product_ids:
            product_vals = {
                'list_price' : item_price,
                'sale_ok' : 'TRUE',
                'name' : product_details['name'],
                'type' : 'product',
                'cost_method' : 'standard',
                'default_code': product_details['sku'],
            }
            prod_id = prod_obj.create(product_vals)
        else:
            prod_id = product_ids[0]
        return prod_id

    
    
    @api.multi
    def createOrder(self, resultval, partner_id_update, billing_id_update, log_id):
        saleorderid = False
        saleorder_obj = self.env['sale.order']
        sale_order_line_obj = self.env['sale.order.line']
        picking_obj = self.env['stock.picking']
        stock_transfer_obj = self.env['stock.immediate.transfer']
        account_invoice_obj = self.env['account.invoice']
        product_obj = self.env['product.product']
        partner_obj = self.env['res.partner']
        payment_obj = self.env['payment.method']
        mage_payment_obj = self.env['payment.method.magento']
        magento_log_line = self.env['magento.log.details']
        data = self
#         try:
        if billing_id_update == False:
            billing_id_update = partner_id_update
        if resultval['created_at']:
            date_from = time.strftime('%Y-%m-%d', time.strptime(resultval['created_at'], '%Y-%m-%d %H:%M:%S'))
            update_date = time.strftime('%Y-%m-%d', time.strptime(resultval['updated_at'], '%Y-%m-%d %H:%M:%S'))
            order_policy = 'manual'
            paid = False
            confirm_order = False 
            payment_ids = payment_obj.search([])
            for payment_data in payment_ids:
                payment_method_pay = payment_data.name.split(',')
                if resultval['payment']['method'] in payment_method_pay:
                    order_policy = payment_data.order_policy
                    paid = payment_data.pay_invoice
                    confirm_order = payment_data.val_order
                    break
        if resultval['state'].find('pending') != -1:
            paid = False
        for each_comment in resultval['status_history']:
            if hasattr(each_comment , 'comment'):
                customer_note = each_comment['comment']
            else:
                customer_note = '' 
        saleorderid = saleorder_obj.search([('mage_order_id', '=', resultval['increment_id']), ('warehouse_id', '=', data.id)])
        prefix = ''
        if data.prefix:
            prefix = data.prefix
        pay_ids = mage_payment_obj.search([('code', '=', resultval['payment']['method'])])
        if pay_ids:
            pid = pay_ids[0]
        else:
            pid = mage_payment_obj.create({'name': resultval['payment']['method'], 'code':resultval['payment']['method']})
        if not saleorderid:
            pricelist_id = partner_id_update[0].property_product_pricelist.id
            order_state = resultval['state']

            if billing_id_update[0] == False:
                billing_id_update = partner_id_update[0].id
            else:
                billing_id_update = billing_id_update[0].id
            if partner_id_update[0] == False:
                partner_id_update = []
            else:
                partner_id_update = partner_id_update[0].id
            ordervals = {
                'name' :prefix + str(resultval['increment_id']),
                'mage_order_id' :str(resultval['increment_id']),
                'created_date':date_from,
                'updated_date':update_date,
                'date_order' :date_from,
                'partner_id' : billing_id_update,
                'partner_shipping_id' : partner_id_update,
                'partner_invoice_id' : billing_id_update,
                'state' : 'draft',
                'pricelist_id' : pricelist_id,
                'picking_policy':'one',
                'invoice_quantity':'order',
                'payment_method': pid.id,
#                     'carrier_id':False,
                'note':customer_note,
                'magento_status':str(resultval['status']),
                'magento_order' : True,
                'magento_order_id' : str(resultval['order_id']),
                'store_id': self[0].id,
            }

            if self.workflow_id:
                if self.workflow_id.warehouse_id:
                    ordervals.update({
                        'warehouse_id':self.workflow_id.warehouse_id.id
                        })
                if self.workflow_id.pricelist_id:

                    ordervals.update({
                        'pricelist_id':self.workflow_id.pricelist_id.id
                        })
                if self.workflow_id.company_id:
                    ordervals.update({
                        'company_id':self.workflow_id.company_id.id
                        })
            saleorder_id = saleorder_obj.create(ordervals)
            tax_id = False
            for each_result in resultval['items']:
                if float(each_result['original_price']) != 0.0:
                    if hasattr(each_result , 'sku'):
                        product_id = self.createUpdateProduct(each_result)
                        product_data = product_id[0]
                        orderlinevals = {
                                'order_id' : saleorder_id.id,
                                'product_uom_qty' : each_result['qty_ordered'],
                                'product_uom' :product_data.product_tmpl_id.uom_id.id,
                                'name' : each_result['name'],
                                'price_unit' : each_result['original_price'],
                                'discount':each_result['discount_percent'],
                                'state' : 'draft',
                                'product_id' : product_id[0].id,
                        }
                        # Create/Update Add Tax
                        if hasattr(each_result , 'tax_percent') and float(each_result['tax_percent']) > 0.0:
                            tax_id = self.getTaxesAccountID(each_result)
                            tax_id
                            if tax_id:
                                orderlinevals['tax_id'] = [(6, 0, [tax_id[0].id])]
                        id = False
                        id = sale_order_line_obj.create(orderlinevals)
            if float(resultval['shipping_amount']) > 0.00:
                prod_shipping_ids = product_obj.search([('default_code', '=', 'SHIP MAGENTO')])
                if not prod_shipping_ids:
                    raise UserError(_('Please Configure shipping product with default code SHIP MAGENTO'))
                prod_shipping_id = prod_shipping_ids[0]
                shiporderlinevals = {
                    'order_id' : saleorder_id.id,
                    'product_uom_qty' : 1,
                    'product_uom' : prod_shipping_ids.product_tmpl_id.uom_id.id,
                    'name' : resultval['shipping_description'],
                    'price_unit' : float(resultval['shipping_amount']),
                    'state' : 'draft',
                    'product_id' : prod_shipping_id.id,
                    }
                if hasattr(each_result , 'tax_percent') and float(each_result['tax_percent']) > 0.0:
                    tax_id = self.getTaxesAccountID(each_result)
                    tax_id
                    if tax_id:
                        orderlinevals['tax_id'] = [(6, 0, [tax_id[0].id])]
                sale_order_line_obj.create(shiporderlinevals)
            if float(resultval['discount_amount']) < 0.00:
                prod_discount_ids = product_obj.search([('default_code', '=', 'DISCOUNT MAGENTO')])
                prod_discount_id = prod_discount_ids[0]

                discountorderlinevals = {
                    'order_id':saleorder_id.id,
                    'product_uom_qty':1,
#                    'product_uom':product_obj.browse(cr,uid,prod_discount_id).product_tmpl_id.id,
#                         'name':resultval[''],
                    'price_unit':float(resultval['discount_amount']),
                    'product_id' : prod_discount_id.id,
                    }
                if hasattr(each_result , 'tax_percent') and float(each_result['tax_percent']) > 0.0:
                    tax_id = self.getTaxesAccountID(each_result)
                    tax_id
                    if tax_id:
                        orderlinevals['tax_id'] = [(6, 0, [tax_id[0].id])]
                sale_order_line_obj.create(discountorderlinevals)
            self._cr.commit()
            if self.workflow_id.validate_order == True and self.workflow_id.reserve_qty == True and self.workflow_id.complete_shipment == True and self.workflow_id.validate_invoice == True and self.workflow_id.register_payment == True:
                if  saleorder_id.state in ['draft','sent']:
                    saleorder_id.action_confirm()
                    for picking_id in saleorder_id.picking_ids:
                        if picking_id.state == 'draft':
                            picking_id.action_confirm()
                        if picking_id.state != 'done':
                            picking_id.button_validate()
                            wiz = self.env['stock.immediate.transfer'].create(
                                {'pick_ids': [(4, picking_id.id)]})
                            wiz.process()
                        # picking_id.action_confirm()
                        # picking_id.action_assign()
                        # picking_id.force_assign()
                        # picking_id.do_transfer()
                    if not saleorder_id.invoice_ids:
                        invoice_id_new = saleorder_id.action_invoice_create()
                    for invoice_id in saleorder_id.invoice_ids:
                        if invoice_id.state not in ['paid']and invoice_id.invoice_line_ids:
                            invoice_id.action_invoice_open()
                            invoice_id.pay_and_reconcile(self.workflow_id and self.workflow_id.sale_journal or self.env['account.journal'].search([('type', '=', 'bank')], limit=1), invoice_id.amount_total)
                    
                    
            if self.workflow_id.validate_order == True:
                print("validate_order")
                if saleorder_id.state in ['draft','sent']:
                    saleorder_id.action_confirm()
                    print("inside validate order")
                # saleorder_id.action_confirm()
            if self.workflow_id.reserve_qty == True:
                print("reserved  quantity")
#                 self.workflow_id.write({'validate_order':True})
                if not saleorder_id.picking_ids:
                    saleorder_id.action_confirm()
                    # saleorder_id.picking_ids[0].write({'is_magento':True, 'magento_shop':saleorder_id.store_id[0].id})
                    for picking_id in saleorder_id.picking_ids:
                        picking_id.write({'is_magento': True, 'magento_shop': saleorder_id.store_id[0].id})
                        if picking_id.state == 'draft':
                            picking_id.action_confirm()
                        if picking_id.state != 'done':
                            picking_id.button_validate()
                            wiz = self.env['stock.immediate.transfer'].create(
                                {'pick_ids': [(4, picking_id.id)]})
                            wiz.process()
                        # picking_id.action_assign()
                        # picking_id.force_assign()
                    
            if self.workflow_id.complete_shipment == True:
                print("completer shipment")
                if saleorder_id.state in ['draft','sent']:
                    saleorder_id.action_confirm()
                for picking_id in saleorder_id.picking_ids:

                    # If still in draft => confirm and assign
                    if picking_id.state == 'draft':
                        picking_id.action_confirm()
                    if picking_id.state != 'done':
                        picking_id.button_validate()
                        wiz = self.env['stock.immediate.transfer'].create({'pick_ids': [(4, picking_id.id)]})
                        wiz.process()

            elif self.workflow_id.create_invoice == True:
                print("create ivoice")
                if saleorder_id.state in ['draft', 'sent']:
                    saleorder_id.action_confirm()
                if not saleorder_id.invoice_ids:
                    # saleorder_id.action_confirm()
                    # saleorder_id.picking_ids[0].write({'is_magento':True, 'magento_shop':saleorder_id.store_id[0].id})
                    # for picking_id in saleorder_id.picking_ids:
                    #     picking_id.action_confirm()
                    #     picking_id.action_assign()
                    #     picking_id.force_assign()
                    #     picking_id.do_transfer()
                    invoice_id_new = saleorder_id.action_invoice_create()
                    # saleorder_id.invoice_ids[0].write({'is_magento':True, 'invoice_store_id':saleorder_id.store_id[0].id})
            if self.workflow_id.validate_invoice == True:
                print("validate invoice")
                if saleorder_id.state in['draft','sent']:
                    saleorder_id.action_confirm()

                if not saleorder_id.invoice_ids:
                    saleorder_id.action_invoice_create()

                for invoice_id in saleorder_id.invoice_ids:
                    if invoice_id.state in['draft','sent']:
                        invoice_id.action_invoice_open()
                # if not saleorder_id.invoice_ids:
                #     saleorder_id.action_confirm()
                #     saleorder_id.picking_ids.write({'is_magento':True, 'magento_shop':saleorder_id.store_id[0].id})
                #     for picking_id in saleorder_id.picking_ids:
                #         picking_id.action_confirm()
                #         picking_id.action_assign()
                #         picking_id.force_assign()
                #         picking_id.do_transfer()
                #     invoice_id_new = saleorder_id.action_invoice_create()
                #     saleorder_id.invoice_ids.write({'is_magento':True, 'invoice_store_id':saleorder_id.store_id[0].id})
                #     for invoice_id in saleorder_id.invoice_ids:
                #         invoice_id.action_invoice_open()

            if self.workflow_id.register_payment == True:
                print("inside register_payment invoice")
                if saleorder_id.state in['draft','sent']:
                    saleorder_id.action_confirm()
                if not saleorder_id.invoice_ids:
                    saleorder_id.action_invoice_create()
                for invoice_id in saleorder_id.invoice_ids:
                    if invoice_id.state == 'draft':
                        invoice_id.action_invoice_open()
                    if invoice_id.state not in ['paid'] and invoice_id.invoice_line_ids:
                        invoice_id.pay_and_reconcile(
                            self.workflow_id and self.workflow_id.sale_journal or self.env[
                                'account.journal'].search(
                                [('type', '=', 'bank')], limit=1), invoice_id.amount_total)

                #                     elif shop_data.workflow_id.register_payment==True:
                #                         if not saleorder_id.invoice_ids:
                #                             saleorder_id.action_confirm()
                #                             invoice_id = saleorder_id.action_invoice_create()
                #                             for invoice_id in saleorder_id.invoice_ids:
                #                                 invoice_id.action_invoice_open()
                #                                 if invoice_id.state not in ['paid']and invoice_id.invoice_line_ids:
                #                                     invoice_id.action_invoice_open()
                #                                     invoice_id.pay_and_reconcile(self.workflow_id and self.workflow_id.sale_journal or self.env['account.journal'].search([('type', '=', 'bank')], limit=1), invoice_id.amount_total)
            self._cr.commit()
            self.write({'magento_order_date': date.today()})

            # if self.workflow_id.register_payment == True:
            #     saleorder_id.action_confirm()
            #     saleorder_id.picking_ids[0].write({'is_magento':True, 'magento_shop':saleorder_id.store_id[0].id})
            #     for picking_id in saleorder_id.picking_ids:
            #             picking_id.action_confirm()
            #             picking_id.action_assign()
            #             picking_id.force_assign()
            #             picking_id.do_transfer()
            #     if not saleorder_id.invoice_ids:
            #         saleorder_id.action_invoice_create()
            #         saleorder_id.invoice_ids[0].write({'is_magento':True, 'invoice_store_id':saleorder_id.store_id[0].id})
            #         for invoice_id in saleorder_id.invoice_ids:
            #             if invoice_id.state not in ['paid']and invoice_id.invoice_line_ids:
            #                 invoice_id.action_invoice_open()
            #                 invoice_id.pay_and_reconcile(self.workflow_id and self.workflow_id.sale_journal or self.env['account.journal'].search([('type', '=', 'bank')], limit=1), invoice_id.amount_total)
#         except Exception as exc:
#             logger.error('Exception===================:  %s', exc)
#             magento_log_line.create({'name':'Import Order', 'description':exc, 'create_date':date.today(),
#                                       'magento_log_id':log_id.id})
#             log_id.write({'description': 'Something went wrong'}) 
#             pass
        return True
    
    
    @api.multi
    def import_invoice(self):
        sale_obj = self.env['sale.order']
        invoice_obj = self.env['account.invoice']
        for shop_data in self:
            mage = Magento(shop_data.magento_instance_id.location, shop_data.magento_instance_id.apiusername, shop_data.magento_instance_id.apipassoword)
            mage.connect()
            order_invoice_lists = mage.client.service.salesOrderInvoiceList(mage.token)
            for invoice_list in order_invoice_lists:
                print("invoice_list", invoice_list)
                order_item = mage.client.service.salesOrderInvoiceInfo(mage.token, invoice_list.increment_id)
                print("order_item", order_item.order_increment_id)
                if order_item:
                    saleorder_id = sale_obj.search([('mage_order_id', '=', order_item.order_increment_id), ('store_id', '=', self.id)])
                    print("saleorder_id",saleorder_id)
                    if saleorder_id:
                        invoice_ids = invoice_obj.search([('origin', '=', saleorder_id.name)])
                        print("invoice_ids=",invoice_ids)
                        if invoice_ids.state == 'paid':
                            pass
                        else:
                            if saleorder_id.state in ['draft','sent']:
                                saleorder_id.action_confirm()
                            saleorder_id.write({'invoiced':True})
                            if not saleorder_id.invoice_ids:
                                print("saleorder_id--invoice", saleorder_id.invoice_ids)
                                saleorder_id.action_invoice_create()
                                for invoice_id in saleorder_id.invoice_ids:
                                    print("invoice_id==",invoice_id)
                                    if invoice_id.state not in ['paid']and invoice_id.invoice_line_ids:
                                        invoice_id.action_invoice_open()
                                        invoice_id.pay_and_reconcile(self.workflow_id and self.workflow_id.sale_journal or self.env['account.journal'].search([('type', '=', 'bank')], limit=1), invoice_id.amount_total)
                        self._cr.commit()
        return True
    
    @api.multi
    def import_shipment(self):
        sale_obj = self.env['sale.order']
        stock_obj = self.env['stock.picking']
        for shop_data in self:
            mage = Magento(shop_data.magento_instance_id.location, shop_data.magento_instance_id.apiusername, shop_data.magento_instance_id.apipassoword)
            mage.connect()
            order_shipment_lists = mage.client.service.salesOrderShipmentList(mage.token)
            for shipment_list in order_shipment_lists:
                print("shipment_list", shipment_list)
                shipped_item = mage.client.service.salesOrderShipmentInfo(mage.token, shipment_list.increment_id)
                if shipped_item:
                    saleorder_id = sale_obj.search([('magento_order_id', '=', shipped_item.order_id), ('store_id', '=', self.id)])
                    print("saleorder_id", saleorder_id)
                    if saleorder_id:
                        stock_ids = stock_obj.search([('origin', '=', saleorder_id.name)])
                        if stock_ids.state == 'done':
                            pass
                        else:
                            saleorder_id.action_confirm()
                            saleorder_id.write({'shipped':True})
                            print("saleorder_id",saleorder_id.shipped)
                            for picking_id in saleorder_id.picking_ids:
                                print("picking_id",picking_id)
                                if picking_id.state == 'draft':
                                    picking_id.action_confirm()
                                if picking_id.state != 'done':
                                    picking_id.button_validate()
                                    wiz = self.env['stock.immediate.transfer'].create(
                                        {'pick_ids': [(4, picking_id.id)]})
                                    wiz.process()
                        self._cr.commit()
                                # picking_id.action_confirm()
                                # picking_id.action_assign()
                                # picking_id.force_assign()
                                # picking_id.do_transfer()
        return True
    
    @api.one
    def getTaxesAccountID(self, each_result):
        accounttax_obj = self.env['account.tax']
        accounttax_id = False
        shop_data = self
        if hasattr(each_result , 'tax_percent') and float(each_result['tax_percent']) > 0.0:
            amount = float(each_result['tax_percent'])
            name = 'Sales Tax(' + str(each_result['tax_percent'] + '%)')
            acctax_ids = self.env['account.tax'].search([('type_tax_use', '=', 'sale'), ('amount', '=', amount), ('name', '=', name)])
            if not len(acctax_ids):
                accounttax_id = accounttax_obj.create({'name':'Sales Tax(' + str(each_result['tax_percent']) + '%)', 'amount':amount, 'type_tax_use':'sale'})
            else:
                accounttax_id = acctax_ids[0]
            
        return accounttax_id
#
    @api.one
    def export_order_status(self):
        stock_obj = self.env['stock.picking']
        invoice_obj = self.env['account.invoice']
        sale_obj = self.env['sale.order']
        magento_log = self.env['magento.log']
        magento_log_line = self.env['magento.log.details']
        log_id = magento_log.create({'create_date':date.today(), 'name': 'Export Order Status', 'description': 'Successfull'})
        shop_data = self
        try:
            mage = Magento(shop_data.magento_instance_id.location, shop_data.magento_instance_id.apiusername, shop_data.magento_instance_id.apipassoword)
            mage.connect()
            today = datetime.datetime.now()
            now = datetime.datetime.now()
            update = now.strftime("%Y-%m-%d")
            order_ids = sale_obj.search(['|', ('magento_status', '=', 'pending'), ('magento_status', '=', 'processing'), ('shipped', '=', False)])
            logger.error('delivery_data %s', order_ids)
            data = []
            for order_data in order_ids:
                try:
                    logger.error('delivery_data %s', order_data)
                    if self.workflow_id.ship_expo_magen == 'oncreation':
                        dilivery_ids = stock_obj.search([('origin', '=', order_data.name), ('state', '!=', 'done')])
                    elif self.workflow_id.ship_expo_magen == 'done':
                        dilivery_ids = stock_obj.search([('origin', '=', order_data.name), ('state', '=', 'done')])
                    shipmentIncrementId = order_data.mage_order_id
                    if dilivery_ids:
                        delivery_data = dilivery_ids
                        logger.error('shipmentIncrementId %s', shipmentIncrementId)
                        if not shipmentIncrementId or not delivery_data.carrier_tracking_ref or not delivery_data.carrier_id.magento_code:
                            raise UserError(_('Error'), _('Please Enter Tracking Ref and Carrier'))
                        else:
                            for stock_data in delivery_data.move_lines:
                                prod_magento_id = stock_data.product_id.magento_id
                                prod_qty = stock_data.product_uom_qty
                                data += [prod_magento_id, prod_qty]
                            shiping_id = mage.client.service.salesOrderShipmentCreate(mage.token, shipmentIncrementId, data)
                            logger.error('shiping_id %s', shiping_id)
                            order_data.write({'shipped':True})

                        if not shiping_id in ['102', '103', '100']:
                            if not delivery_data.carrier_id or not delivery_data.carrier_id.magento_code:
                                raise  UserError(_('Error'), _('Please Enter Carrier Delivery'))
                            else:
                                carrier = delivery_data.carrier_id.magento_code
                                title = delivery_data.carrier_id.name
                                trackNumber = delivery_data.carrier_tracking_ref
                                logger.error('trackNumber %s', trackNumber)
                                track = mage.client.service.salesOrderShipmentAddTrack(mage.token, shiping_id, carrier, title, trackNumber)
                                logger.error('track %s', track)
                except Exception as exc:
                    logger.error('Exception===================:  %s', exc)
                    magento_log_line.create({'name':'Export Order Status', 'description':exc, 'create_date':date.today(),
                                              'magento_log_id':log_id.id})
                    log_id.write({'description': 'Something went wrong'}) 
                    pass
            order_ids = sale_obj.search(['|', ('magento_status', '=', 'pending'), ('magento_status', '=', 'processing'), ('invoiced', '=', False)])
            logger.error('order_ids for invoice %s', order_ids)
            for order_data in order_ids:
                try:
                    itemsQty = {}
                    for line in order_data.order_line:
                        item_qty = line.product_uom_qty
                        order_item_qty = line.product_id.magento_id
                        itemsQty = {'order_item_id' :order_item_qty , 'qty' : item_qty }
                        data += [order_item_qty, item_qty]
                    if self.workflow_id.invoice_expo_magen == 'oncreation':
                        inv_ids = invoice_obj.search([('origin', '=', order_data.name), ('state', '=', 'draft')])
                    elif self.workflow_id.invoice_expo_magen == 'after_validation':
                        inv_ids = invoice_obj.search([('origin', '=', order_data.name), ('state', '=', 'open')])
                    elif self.workflow_id.invoice_expo_magen == 'done':
                        inv_ids = invoice_obj.search([('origin', '=', order_data.name), ('state', '=', 'paid')])
                    logger.error('inv_ids for invoice %s', inv_ids)
                    shipmentIncrementId = order_data.mage_order_id
                    if inv_ids:
                        logger.error('shipmentIncrementId', shipmentIncrementId)
                        invv_id = mage.client.service.salesOrderInvoiceCreate(mage.token, shipmentIncrementId, data)
                        print( 'invv_id++++++++++++++++++' , invv_id)
                        logger.error('invv_id', invv_id)
                        order_data.write({'magento_status':'complete', 'invoiced': True})
                except Exception as exc:
                    logger.error('Exception===================:  %s', exc)
                    magento_log_line.create({'name':'Export Order Status', 'description':exc, 'create_date':date.today(),
                                              'magento_log_id':log_id.id})
                    log_id.write({'description': 'Something went wrong'}) 
                    pass
                    logger.error('Export Order Exception:  %s', exc)
                self.write({'start_date':update})
        except Exception as exc:
            logger.error('Exception===================:  %s', exc)
            log_id.write({'description': exc})
            pass
        return True




