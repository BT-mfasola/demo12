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
                                                                            #
#                                                                            #
##############################################################################

from odoo import models, fields, api, _
from . PyMagento import Magento
import socket
from odoo.tools.translate import _
# import cStringIO # *much* faster than StringIO
# import urllib
import urllib.request as urllib
from PIL import Image
import os
# from urllib import urlencode
import base64
import time
import datetime
from datetime import date, timedelta
from odoo import netsvc
from suds.client import Client
from odoo.exceptions import UserError
import logging
logger = logging.getLogger('product')
# from clint.textui import colored


class magento_instance(models.Model):
    _name = 'magento.instance'
   
    name = fields.Char('Name',size=64, required=True)
    magento_default_pro_cat  =fields.Many2one('product.category','Default Product Category')
    product_uom = fields.Many2one('product.uom','Unit of Product Measure')
    location = fields.Char('Location',size=128, required=True)
    apiusername = fields.Char('user Name',size=64, required=True)
    apipassoword = fields.Char('password',size=64, required=True)
    default_lang_id = fields.Many2one('res.lang', 'Default Language')
    test_success=fields.Char(readonly=True)
    test_fail=fields.Char(readonly=True)
    check_instance=fields.Boolean('Checked')
    check_button=fields.Boolean('Checked')
    color=fields.Boolean()
    state=fields.Selection([('test','Test'),
                            ('failed','Failed'),
                            ('success','Success')],default='test')
    export_stock_date = fields.Date('Date of Export Stock')
    export_stock_del = fields.Boolean('Export Stock On Delivery Orders')
    export_stock_inv = fields.Boolean('Export Stock On Incoming Shipment')
    order_place = fields.Date('Date of Import Stock')
    last_update_cust = fields.Date('Date of Last Update Customer')
    last_update_cust_grp = fields.Date('Date of Last Update Customer Group')
    inventory_location_id = fields.Many2many('stock.location', string='Inventory Location',)


    @api.multi
    def get_carrier(self):
        for shop_data in self:
            mage = Magento(shop_data.location,shop_data.apiusername,shop_data.apipassoword)
            mage.connect()
            delivery_id = mage.client.service.salesOrderShipmentGetCarriers(mage.token)
        return True

    @api.one
    def test_connection(self):
        (instances,) = self     
        print("instances.location",instances.location,instances.apiusername,instances.apipassoword)
        mage = Magento(instances.location,instances.apiusername,instances.apipassoword)
        print("mage",mage)
#         try:
        mage.connect()
        if mage.connect:
            s="Test Connection Successful, You can proceed with your synchronization"
            self.write({'test_success':s, 'state':'success','color':True})
#         except Exception as e:
#             self.write({'test_fail':"Test Connection Failed, Please check your credentials",'state':'failed','color':False})
  
  
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        def get_view_id(xid, name):
            try:
                return self.env.ref('globalteckz_magento.' + xid)
            except ValueError:
                view = self.env['ir.ui.view'].search([('name', '=', name)], limit=1)
                if not view:
                    return False
                return view.id
        context = self._context 
        if not view_type:
            view_id = get_view_id('globalteckz_magento.magento_instance_form_tree', 'globalteckz_magento.magento.instance.tree')
            view_type = 'tree'
        elif view_type == 'form':
            if 'default_check_instance' in context:
                var1=context['default_check_instance']
                if var1:
                    view_id = get_view_id('globalteckz_magento.magento_instance_form_view', 'Magento Instance')
            elif 'default_check_button' in context:
                var2=context['default_check_button']
                if var2:
                    view_id = get_view_id('globalteckz_magento.magento_instance_inherit', 'Magento Instance1')
               
        return super(magento_instance, self).fields_view_get(view_id=view_id, view_type=view_type)
    
    
    @api.one
    def create_stores(self):
        magento_log = self.env['magento.log']
        magento_log_line = self.env['magento.log.details']
        log_id = magento_log.create({'create_date':date.today(),'name': 'Create Stores','description': 'Successfull'})
        try:
            mage = Magento(self.location,self.apiusername,self.apipassoword)
            mage.connect()
            store_list = mage.client.service.storeList(mage.token)
            for each_store in store_list:
                try:
                    shop_ids = self.env['magento.shop'].search([('code','=',each_store['code']),('store_id','=',each_store['store_id']),('name','=',each_store['name']),('magento_instance_id','=',self.id)])
                    if not len(shop_ids):
                        payment_ids = self.env['account.payment.term'].search([])
                        if not payment_ids:
                            raise except_orm(_('Error'), _('No Payment Terms Defined'))
                           
                        update_vals = {
                                    'magento_code':each_store['code'],
                                    'code':each_store['code'],
                                    'store_id':each_store['store_id'],
                                    'name':each_store['name'],
                                    'website_id':each_store['website_id'],
                                    'magento_shop':True,
                                    'magento_instance_id':self.id,
                                }
                        shop_id=self.env['magento.shop'].create(update_vals)
                        self.update({'color' : True})
                except Exception as exc:
                    logger.error('Exception===================:  %s', exc)
                    magento_log_line.create({'name':'Create Stores','description':exc,'create_date':date.today(),
                                              'magento_log_id':log_id.id})
                    log_id.write({'description': 'Something went wrong'}) 
                    pass   
        except Exception as exc:
            logger.error('Exception===================:  %s', exc)
            log_id.write({'description': exc})
            pass
        return True
    
    @api.one
    def import_products(self):
        print ("inside the import product function is calling////////////////////")
        magento_log = self.env['magento.log']
        magento_log_line = self.env['magento.log.details']
        log_id = magento_log.create({'create_date':date.today(),'name': 'Import Product','description': 'Successfull'})
        prod_obj=self.env['product.product']
        (instances,) = self
        # try:
        mage = Magento(instances.location,instances.apiusername,instances.apipassoword)
        mage.connect()
        list_prods = mage.client.service.catalogProductList(mage.token)
        print ('list_prods9999999+++++',len(list_prods))
        prod_obj.create_products(list_prods,instances,log_id)
        # except Exception as exc:
        #     logger.error('Exception===================:  %s', exc)
        #     log_id.write({'description': exc})
        #     pass
        return True

    @api.one
    def import_att_list(self):
        magento_log = self.env['magento.log']
        magento_log_line = self.env['magento.log.details']
        attribute_obj = self.env['magerp.product_attributes']
        attribute_line_obj = self.env['magerp.product_attribute_line']
        log_id = magento_log.create({'create_date':date.today(),'name': 'Import Attribute List','description': 'Successful'})
        shop_ids = self.env['magento.shop'].search([('magento_instance_id','=',self[0].id)])
        if not len(shop_ids):
            raise  UserError(_('Error'), _('Please Create Store'))
        # try:
        mage = Magento(self.location,self.apiusername,self.apipassoword)
        mage.connect()
        attribute_ids = self.env['magerp.product.attribute.set'].search([])
        logger.error('attribute_idsss %s', attribute_ids)
        if not len(attribute_ids):
            raise  UserError(('Please Import AttributeSet'))
        attributes_list_id = []
        for attribute_data in attribute_ids:
            # try:
            attributes_list = mage.client.service.catalogProductAttributeList(mage.token,attribute_data.code)
            for attribute in attributes_list:
                attribute_oe_ids = attribute_obj.search([('attribute_code','=',attribute.code),('referential_id','=',self.id)])
                print("attribute_oe_ids",attribute_oe_ids)
                if not len(attribute_oe_ids) > 0:
                    attribute_oe_id = attribute_obj.create({'attribute_code':attribute.code,'referential_id':self.id})
                    if len(attribute_oe_id) > 0:
                        attribute_line_id = attribute_line_obj.search([('attribute_id_data','=',attribute_oe_id.id),('attribute','=',attribute_data.id)])
                        if not len(attribute_line_id) > 0:
                            attribute_line = attribute_line_obj.create({'attribute_id_data':attribute_oe_id.id, 'attribute':attribute_data.id})
                else:
                    attribute_oe_id = attribute_oe_ids
                    if len(attribute_oe_id) > 0:
                        attribute_line_id = attribute_line_obj.search([('attribute_id_data','=',attribute_oe_ids.id),('attribute','=',attribute_data.id)])
                        if not len(attribute_line_id) > 0:
                            attrbiute_line = attribute_line_obj.create({'attribute_id_data':attribute_oe_ids.id, 'attribute':attribute_data.id})
                            print("attribute line in else condition",attrbiute_line)
                self._cr.commit()
                attributes_option_list = mage.client.service.catalogProductAttributeOptions(mage.token,attribute.attribute_id,1)
                for attribute_option in attributes_option_list:
                    if attribute_option.value != 'None':
                        attribute_oe_opt_ids = self.env['magerp.product_attribute_options'].search([('attribute_id','=',attribute_oe_id[0].id),('referential_id','=',self[0].id),('label','=',attribute_option.label)])
                        if not len(attribute_oe_opt_ids):
                            attribute_option_id = self.env['magerp.product_attribute_options'].create({'attribute_id':attribute_oe_id[0].id,'referential_id':self[0].id,'value':attribute_option.value,'label':attribute_option.label,'values':attribute_oe_id[0].id})
                            print( "attribute_option_id",attribute_option_id)
                        self._cr.commit()
                # except Exception as exc:
                #     logger.error('Exception===================:  %s', exc)
                #     magento_log_line.create({'name':'Import Attribute List','description':exc,'create_date':date.today(),
                #                               'magento_log_id':log_id.id})
                #     log_id.write({'description': 'Something went wrong'})
                #     pass

        # except Exception as exc:
        #     logger.error('Exception===================:  %s', exc)
        #     log_id.write({'description': exc})
        #     pass
        return True
        
                           
    @api.one
    def import_att_set(self):
        magento_log = self.env['magento.log']
        magento_log_line = self.env['magento.log.details']
        log_id = magento_log.create({'create_date':date.today(),'name': 'Import Attribute Set','description': 'Successfull'})
        magento_field_set_obj= self.env['magerp.product.attribute.set']
        shop_obj= self.env['magento.shop']
        shop_id=shop_obj.search([('magento_instance_id','=',self[0].id)])
        if not shop_id:
            raise  UserError(_('Error'), _('Please Create Store'))
        try:
            mage = Magento(self.location,self.apiusername,self.apipassoword)
            mage.connect()
            list_prods=mage.client.service.catalogProductAttributeSetList(mage.token)
            for list_prod in list_prods:
                print ("list_prod//////////////",list_prod)
                try:
                    val={
                        'name':list_prod['name'],
                        'code':list_prod['set_id'],
                        #'shop_id':shop_id.id
                        'instance_id':self.id,
                        }
                    data_att_id=magento_field_set_obj.search([('name','=',list_prod['name'])])
                    print ("yahooooooooooooooooooooooooooooooooooo",data_att_id)
                    if data_att_id:
                        data_att_id.write(val)
                    else:
                        data_att_id.create(val)
                except Exception as exc:
                    logger.error('Exception===================:  %s', exc)
                    magento_log_line.create({'name':'Import Attribute Set','description':exc,'create_date':date.today(),
                                              'magento_log_id':log_id.id})
                    log_id.write({'description': 'Something went wrong'}) 
                    pass
        except Exception as exc:
            logger.error('Exception===================:  %s', exc)
            log_id.write({'description': exc})
            pass
        return True

    @api.one
    def import_image(self):
        magento_log = self.env['magento.log']
        log_id = magento_log.create({'create_date':date.today(),'name': 'Import Image','description': 'Successfull'})
        pro_obj=self.env['product.product']
        shop_obj=self.env['magento.shop']
        image_obj=self.env['product.images']
        (mag_id,) = self
        shop_ids=shop_obj.search([])
        if not shop_ids:
            raise  UserError(_('Error'), _('Please Create Store'))
        mage = Magento(mag_id.location,mag_id.apiusername,mag_id.apipassoword)
        mage.connect()
        offset = 0
        product_ids = [1]
        while(product_ids):
            product_ids=pro_obj.search([('type','!=','service'),('active','=',True),('select_instance','=',self.id)],offset, 100, 'id')
            print("product_ids===",product_ids)
            if not product_ids: break
            offset += len(product_ids)
            for prod_data in product_ids:
               try:
                    logger.error('SKU:  %s', prod_data.default_code)
                    if prod_data.default_code:
                        list_prods = mage.client.service.catalogProductAttributeMediaList(mage.token,prod_data.default_code,1,'sku')
                        logger.error('list_prods:  %s', list_prods)
                        if list_prods != '101':
                            if len(list_prods):
                                print ("len(list_prods)",len(list_prods))
                                self.create_image(prod_data,list_prods,log_id)
               except Exception as exc:
                   logger.error('Exception===================:  %s', exc)
                   log_id.write({'description': exc})
                   pass
        return True
    
    @api.one
    def create_image(self,prod_data,list_prods,log_id):
        img_obj=self.env['product.images']
        magento_log_line = self.env['magento.log.details']
        prod_obj=self.env['product.product']
        try:
            for list_prod in list_prods:
                if list_prod['url']:
                    file = urllib.urlopen(list_prod['url'])
                    ext = list_prod['url'].split('.')[-1]
                    image_name=list_prod['file'].split('.')[0].split('/')[-1]
                    vals = {
                            'magento_url':list_prod['file'],
                            'name':list_prod['label'],
                            'link': 1,
                            'url':list_prod['url'],
                            'product_id': prod_data.id,
                            'is_exported':True,
                    }
                    for image_type in list_prod['types']:
                        if 'image' in image_type:
                            vals.update({'image':True})
                        if 'small_image' in image_type:
                            vals.update({'small_image':True})
                        if 'thumbnail' in image_type:
                            vals.update({'thumbnail':True})

                    data_img_id=img_obj.search([('name','=',image_name),('product_id','=',prod_data.id)])
                    if data_img_id:
                        image_id = data_img_id.write(vals)
                    else:
                        image_id =img_obj.create(vals)
                        if image_id[0].link==True:
                            file_data = urllib.urlopen(image_id.url).read()
                            image_path = base64.encodestring(file_data)
                            image_id = image_id.write({'file_db_store':image_path})
                image_data=img_obj.search([('product_id','=',prod_data.id)])
                if image_data[0].link== True:
                    file_contain = urllib.urlopen(image_data[0].url).read()
                    image_path = base64.encodestring(file_contain)
                else:
                    image_path = image_data[0].file_db_store
                update=prod_data.write({'image_medium':image_path})
        except Exception as exc:
           logger.error('Exception===================:  %s', exc)
           magento_log_line.create({'name':'Import Image','description':exc,'create_date':date.today(),
                                     'magento_log_id':log_id.id})
           log_id.write({'description': 'Something went wrong'})
           pass
        self._cr.commit()
        return True


    @api.one
    def record_entire_tree(self,categ_tree , mage,name,log_id):
        imp_vals=self.record_category(int(categ_tree['category_id']),mage,name,log_id)
        for each in categ_tree['children']:
            print ('each+++++++++++++++',each)
            self.record_entire_tree(each,mage,name,log_id)
        return True


    @api.one
    def record_category(self,category_id ,mage,name,log_id):
        prod_cat_obj= self.env['product.category']
        imp_vals = mage.client.service.catalogCategoryInfo(mage.token,category_id)
        prod_cat_obj.create_cat(imp_vals,mage,name,log_id)
        return True
    
    @api.one
    def import_cat(self):
        magento_log = self.env['magento.log']
        log_id = magento_log.create({'create_date':date.today(),'name': 'Import Category','description': 'Successfull'})
        try:
            shop_obj= self.env['magento.shop']
            shop_id=shop_obj.search([('magento_instance_id','=',self.id)])[0]
            if not shop_id:
                raise  UserError(_('Error'), _('Please Create Store'))
            #shop_data=shop_obj.browse(shop_id)
            mage = Magento(self.location,self.apiusername,self.apipassoword)
            mage.connect()
            list_category = mage.client.service.catalogCategoryTree(mage.token)
            print ('list_category+++++++++',list_category)
            instance = self
            self.record_entire_tree(list_category,mage,instance,log_id)
        except Exception as exc:
            logger.error('Exception===================:  %s', exc)
            log_id.write({'description': exc})
            pass
        return True
    
    @api.one
    def import_stock(self):
        magento_log = self.env['magento.log']
        magento_log_line = self.env['magento.log.details']
        stock_warehouse_obj = self.env['stock.warehouse']
        log_id = magento_log.create({'create_date':date.today(),'name': 'Import Stock','description': 'Successfull'})
        pro_obj=self.env['product.product']
        stock_inventory_line_obj=self.env['stock.inventory.line']
        stock_inventory_obj=self.env['stock.inventory']
        try:
            for shop_data in self:
                try:
                    mage = Magento(shop_data.location,shop_data.apiusername,shop_data.apipassoword)
                    mage.connect()
                    inventory_id = stock_inventory_obj.create({'name':'update stock'+' '+str(datetime.datetime.now())})
        #            print inventory_id
                    logger.error('inv_id %s', inventory_id)
                    pro_ids=pro_obj.search([])
                    datas = []
                    for prod_data in pro_ids:
                        if prod_data.magento_id != 0:
                            datas.append(prod_data.default_code)
                    list_prods = mage.client.service.catalogInventoryStockItemList(mage.token,datas)
                    if list_prods:
                        for list_prod in list_prods:
                            product_ids = pro_obj.search([('default_code','=',list_prod['sku']),('active','=',True),('select_instance','=',self.id)])
                            if len(product_ids):
                                print ('list_prod+++++++', list_prod['qty'])
                                logger.error('quantity %s', list_prod['qty'])
                                if float(list_prod['qty']) > 0.0000:
                                    vals={'inventory_id':inventory_id.id,'product_id':product_ids.id,'product_qty':list_prod['qty']}
                                    if shop_data.inventory_location_id:
                                        vals.update({'location_id':self.inventory_location_id.id})
                                    else:
                                        warehouse_ids = stock_warehouse_obj.search([])
                                        print ("warehouse_ids", warehouse_ids)
                                        vals.update({'location_id':warehouse_ids[0].lot_stock_id.id})
                                    stock_inventory_line_obj.create(vals)
                except Exception as exc:
                    logger.error('Exception===================:  %s', exc)
                    magento_log_line.create({'name':'Import Stock','description':exc,'create_date':date.today(),
                                              'magento_log_id':log_id.id})
                    log_id.write({'description': 'Something went wrong'}) 
                    pass
                inventory_id.action_validate()
            shop_data.write({'order_place':date.today()})
        except Exception as exc:
            logger.error('Exception===================:  %s', exc)
            log_id.write({'description': exc})
            pass
        return True
    
    
    @api.one
    def export_stock(self):
        magento_log = self.env['magento.log']
        magento_log_line = self.env['magento.log.details']
        stock_quant_obj = self.env['stock.quant']
        log_id = magento_log.create({'create_date':date.today(),'name': 'Export Stock','description': 'Successfull'})
        pro_obj=self.env['product.product']
        try:
            for shop_data in self:
                mage = Magento(shop_data.location,shop_data.apiusername,shop_data.apipassoword)
                mage.connect()
                pro_ids=pro_obj.search([('select_instance','=',shop_data.id),('magento_exported','=',True),('magento_id','!=','')])
#                 pro_ids=pro_obj.search([('id','=',2646)])
                for prod_data in pro_ids:
                    stock_quant_ids = stock_quant_obj.search([('product_id','=',prod_data.id),('location_id','in',self.inventory_location_id.ids)])
                    print("stock_quant_ids",stock_quant_ids)
                    inv = 0
                    for quant in stock_quant_ids:
                        print("quant",quant)
                        inv+= quant.quantity
                    try:
                        in_stock = 0
                        print ('prod_data.qty_available++++++++', prod_data.qty_available)
                        if int(inv) >= 1:
                            in_stock = 1
                            sku_list = {'qty':inv,'is_in_stock':in_stock}
                            print ('sku_list9+++++++++',) 
                            mage.client.service.catalogInventoryStockItemUpdate(mage.token,prod_data.default_code,sku_list)
                            #shop_data.write({'export_stock_date':date.today()})
                    except Exception as exc:
                        logger.error('Exception===================:  %s', exc)
                        magento_log_line.create({'name':'Export Stock','description':exc,'create_date':date.today(),
                                                  'magento_log_id':log_id.id})
                        log_id.write({'description': 'Something went wrong'}) 
                        pass
            shop_data.write({'export_stock_date':date.today()})
        except Exception as exc:
            logger.error('Exception===================:  %s', exc)
            log_id.write({'description': exc})
            pass
        return True
    
    
    @api.one
    def import_customer_group(self):
        cust_grp_obj=self.env['customer.group']
        magento_log = self.env['magento.log']
        magento_log_line = self.env['magento.log.details']
        log_id = magento_log.create({'create_date':date.today(),'name': 'Import Customer Group','description': 'Successfull'})
        (shop_data,) = self
        try:
            mage = Magento(shop_data.location,shop_data.apiusername,shop_data.apipassoword)
            mage.connect()
            customer_list = [1]
            offset = 1
            customer_list = mage.client.service.customerGroupList(mage.token)
            offset += len(customer_list) + 1
            for customer in customer_list:
                try:
                    data={
                        'name':customer['customer_group_code'],
                        'customer_group_code':customer['customer_group_id'],
                        'instance_id':self.id
                    }
                    cust_grp_id=cust_grp_obj. search([('customer_group_code','=',customer['customer_group_code']),('instance_id','=',self.id)])
                    if not cust_grp_id:
                        grp=cust_grp_obj.create(data)

                    else:
                       grp=cust_grp_id.write(data)
                except Exception as exc:
                        logger.error('Exception===================:  %s', exc)
                        magento_log_line.create({'name':'Import Customer Group','description':exc,'create_date':date.today(),
                                                  'magento_log_id':log_id.id})
                        log_id.write({'description': 'Something went wrong'}) 
                        pass
            shop_data.write({'last_update_cust_grp':date.today()})
        except Exception as exc:
            logger.error('Exception===================:  %s', exc)
            log_id.write({'description': exc})
            pass
        return True
    
    
    @api.one
    def import_customer(self):
        magento_log = self.env['magento.log']
        magento_log_line = self.env['magento.log.details']
        log_id = magento_log.create({'create_date':date.today(),'name': 'Import Customer','description': 'Successfull'})
        instance = self.env['magento.instance']
        shop_data = self
        mage = Magento(shop_data.location,shop_data.apiusername,shop_data.apipassoword)
        mage.connect()
        customer_list = [1]
        offset = 1
        # try:
        while(len(customer_list)):
            if shop_data.last_update_cust:
                value_date = {'key':'gteq','value':shop_data.last_update_cust}
                params = [{'complex_filter':[{'key':'created_at','value':value_date}]}]
            else:
                limit = offset+200
                ids_list = []
                for x in range(offset, limit):
                    ids_list.append(x)
                greater_value = {'key':'in','value':ids_list}
                params = [{'complex_filter':[{'key':'customer_id','value':greater_value}]}]

            customer_list = mage.client.service.customerCustomerList(mage.token,params)
            print("customer_list",customer_list)
            if len(customer_list) == 0:
                break
            offset += len(customer_list) + 1
            for customer in customer_list:
                # try:
                if customer['customer_id']:
                    print("customer['customer_id']",customer['customer_id'])
                    instance = self
                    cust_data =mage.client.service.customerAddressList(mage.token,customer['customer_id'])
                    if cust_data:
                        instance.create_customer(cust_data[0],customer['email'],instance)
                    else:
                        instance.create_name_customer(customer,instance)
                # except Exception as exc:
                #     logger.error('Exception===================:  %s', exc)
                #     magento_log_line.create({'name':'Import Customer','description':exc,'create_date':date.today(),
                #                               'magento_log_id':log_id.id})
                #     log_id.write({'description': 'Something went wrong'})
                #     pass
            if shop_data.last_update_cust:
                break
        shop_data.write({'last_update_cust':date.today()})
        # except Exception as exc:
        #     logger.error('Exception===================:  %s', exc)
        #     log_id.write({'description': exc})
        #     pass
        return True
    
    def create_name_customer(self,resultvals,instance):
        dob,taxvat=False,False
        res_obj=self.env['res.partner']
        name = ''
        if hasattr(resultvals ,'firstname') and hasattr(resultvals ,'lastname'):
            name= resultvals['firstname'] + ' ' + resultvals['lastname']
        elif hasattr(resultvals ,'firstname'):
            name=resultvals['Name']=resultvals['firstname']
        elif hasattr(resultvals ,'lastname'):
            name= resultvals['lastname']
            
        email=resultvals['email']
        if hasattr(resultvals ,'group_id'):
            customer_grp=resultvals['group_id']
        if hasattr(resultvals ,'dob'):
            dob=resultvals['dob']
        if hasattr(resultvals ,'taxvat'):
            taxvat=resultvals['taxvat']
        partner_data = {
            'name' : name or '',
            'email' :email,
            'customer':True,
            'is_a_magento_customer':True,
            'type' : 'contact',
            'opt_out':True,
            'dob':dob,
            'tax_vat':taxvat,
            'customer_grp':customer_grp,
            'instance_id':instance.id,
        }
        partner_ids = res_obj.search([('email','=',email),('instance_id','=',instance.id)])
        if len(partner_ids):
            partner_id =partner_ids[0].write(partner_data)
            partner_id = partner_ids[0]
        else:
            partner_id = res_obj.create(partner_data)
        self._cr.commit()
        return partner_id
  
    def create_customer(self,resultvals,email,instance):
        res_obj=self.env['res.partner']
        prodsupplier_vals={}

        if hasattr(resultvals ,'firstname') and hasattr(resultvals ,'lastname'):
            name= resultvals['firstname'] + ' ' + resultvals['lastname']
        elif hasattr(resultvals ,'firstname'):
            name=resultvals['Name']=resultvals['firstname']
        else:
            name= resultvals['lastname']

        if hasattr(resultvals ,'country_id'):
            if resultvals['country_id']!= 'None' or resultvals['country_id']!= []:
                country_ids = self.env['res.country'].search([('code','=',resultvals['country_id'])])
                if not country_ids:
                    country_id =  self.env['res.country'].create({'code':resultvals['country_id'][:2], 'name':resultvals['country_id']})
                else:
                    country_id = country_ids[0]

        state_id = False
        if hasattr(resultvals ,'region'):
            if resultvals['region']!= 'None' or resultvals['region']== []:
                state_ids = self.env['res.country.state'].search([('name','=',resultvals['region'])])
                if len(state_ids) > 0:
                    state_id = state_ids[0].id
                # else:
                #     state_id = self.env['res.country.state'].create({'country_id':country_ids[0].id, 'name':resultvals['region'], 'code':country_id}).id
        postcode = False
        if hasattr(resultvals ,'postcode'):
            postcode = resultvals['postcode']

        telephone = False
        if hasattr(resultvals ,'telephone'):
            telephone = resultvals['telephone']

        street = False
        if hasattr(resultvals ,'street'):
            street = resultvals['street']

        city = False
        if hasattr(resultvals ,'city'):
            city = resultvals['city']

        addressvals = {
            'name' : name,
            'street' :street,
            'city' : city,
            'country_id' :country_id.id,
            'phone' :telephone,
            'zip' :postcode,
            'state_id' : state_id or False,
            'email' :email,
            'customer':True,
            'is_a_magento_customer':True,
            'type' : 'contact',
            'opt_out':True,
            'instance_id':instance.id,
        }
        partner_address_ids = res_obj.search([('email','=',email),('street','=',street),('zip','=',postcode)])
        if len(partner_address_ids):
            address_id =partner_address_ids[0].write(addressvals)
            address_id = partner_address_ids[0]
        else:
            address_id = res_obj.create(addressvals)
        self._cr.commit()
        return address_id
    
#    def _magento_instance(self, cr, uid, callback, context=None):
#        if context is None:
#            context = {}
#        proxy = self.pool.get('magento.instance')
#        domain = []
#        ids = proxy.search(cr, uid, domain, context=context)
#        if ids:
#            callback(cr, uid, ids, context=context)
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
#    def import_product_scheduler(self, cr, uid, context=None):
#        
#        self._magento_instance(cr,uid,self.import_products,context=context)
#
#    def run_import_products_scheduler(self, cr, uid, context=None):
#        self._magento_instance(cr, uid, self.import_products, context=context)
#        
#    def run_import_stock_levels_scheduler(self, cr, uid, context=None):
#        self._magento_instance(cr, uid, self.import_stock, context=context)
#
#    def run_export_stock_levels_scheduler(self, cr, uid, context=None):
#        self._magento_instance(cr, uid, self.export_stock, context=context)
#    
#    def run_import_customer_scheduler(self, cr, uid, context=None):
#        self._magento_instance(cr, uid, self.import_customer, context=context)
#        
#    def run_import_images_scheduler(self, cr, uid, context=None):
#        self._magento_instance(cr, uid, self.import_image, context=context)
#
#magento_instance()
#
class magerp_product_attribute_set(models.Model):
    _name = "magerp.product.attribute.set"
 
    name = fields.Char('Attribute Set Name',size=64,required=True)
    code= fields.Integer('Code',size=100,required=True)
    attributes = fields.Many2many('magerp.product_attributes', 'magerp_attrset_attr_rel', 'set_id', 'attr_id', 'Attributes')
    shop_id = fields.Many2one('magento.shop','shop')
    attribute_ids = fields.One2many('magerp.product_attributes', 'attr_set_id', 'Attributes')
    attribute_line_id = fields.One2many('magerp.product_attribute_line', 'attribute', 'Attributes')
    instance_id = fields.Many2one('magento.instance', string='Magento Instance')

#
class magerp_product_attributes(models.Model):
    _name = "magerp.product_attributes"
    _description = "Attributes of products"
    _rec_name = "attribute_code"

  
    attribute_code =fields.Char('Code', size=200)
    magento_id  = fields.Integer('ID')
    set_id = fields.Integer('Attribute Set')
    options = fields.One2many('magerp.product_attribute_options', 'attribute_id', 'Attribute Options')
    frontend_input = fields.Selection([
                                           ('text', 'Text'),
                                           ('textarea', 'Text Area'),
                                           ('select', 'Selection'),
                                           ('multiselect', 'Multi-Selection'),
                                           ('boolean', 'Yes/No'),
                                           ('date', 'Date'),
                                           ('price', 'Price'),
                                           ('media_image', 'Media Image'),
                                           ('gallery', 'Gallery'),
                                           ('weee', 'Fixed Product Tax'),
                                           ('file', 'File'), #this option is not a magento native field it will be better to found a generic solutionto manage this kind of custom option
                                           ], 'Frontend Input'
                                          )
    frontend_class = fields.Char('Frontend Class', size=100)
    backend_model = fields.Char('Backend Model', size=200)
    backend_type = fields.Selection([
                                         ('static', 'Static'),
                                         ('varchar', 'Varchar'),
                                         ('text', 'Text'),
                                         ('decimal', 'Decimal'),
                                         ('int', 'Integer'),
                                         ('datetime', 'Datetime')], 'Backend Type')
    frontend_label = fields.Char('Label', size=100)
    is_visible_in_advanced_search = fields.Boolean('Visible in advanced search?', required=False)
    is_global  = fields.Boolean('Global ?', required=False)
    is_filterable =fields.Boolean('Filterable?', required=False)
    is_comparable = fields.Boolean('Comparable?', required=False)
    is_visible =fields.Boolean('Visible?', required=False)
    is_searchable =fields.Boolean('Searchable ?', required=False)
    is_user_defined = fields.Boolean('User Defined?', required=False)
    is_configurable = fields.Boolean('Configurable?', required=False)
    is_visible_on_front = fields.Boolean('Visible (Front)?', required=False)
    is_used_for_price_rules = fields.Boolean('Used for pricing rules?', required=False)
    is_unique = fields.Boolean('Unique?', required=False)
    is_required = fields.Boolean('Required?', required=False)
    position = fields.Integer('Position', required=False)
    group_id = fields.Integer('Group')
    group = fields.Many2one('magerp.product_attribute_groups', 'Attribute Group', readonly=True)
    apply_to = fields.Char('Apply to', size=200)
    default_value = fields.Char('Default Value', size=10)
    note  = fields.Char('Note', size=200)
    entity_type_id = fields.Integer('Entity Type')
    referential_id = fields.Many2one('magento.instance', 'Magento Instance', readonly=True)
        #These parameters are for automatic management
    field_name = fields.Char('Open ERP Field name', size=100)
    attribute_set_info = fields.Text('Attribute Set Information')
    based_on = fields.Selection([('product_product', 'Product Product'), ('product_template', 'Product Template')], 'Based On')
    attr_set_id = fields.Many2one('magerp.product.attribute.set', 'Attribute Set')
    imports = fields.Boolean('Import')
    value_ids = fields.One2many('magerp.product_attribute_options', 'values', 'Value')

#
class magerp_product_attribute_options(models.Model):
    _name = "magerp.product_attribute_options"
    _description = "Options  of selected attributes"
    _rec_name = "value"

    
    attribute_id = fields.Many2one('magerp.product_attributes', 'Attribute')
    attribute_name  = fields.Char( related='attribute_id.attribute_code' , type='char', string='Attribute Code',)
    value  = fields.Char('Value', size=200)
    ipcast = fields.Char('Type cast', size=50)
    label = fields.Char('Label', size=100)
    referential_id = fields.Many2one('magento.instance', 'Magento Instance', readonly=True)
    values = fields.Many2one('magerp.product_attributes')


class magerp_product_attribute_line(models.Model):
    _name = "magerp.product_attribute_line"
 
    attribute_id_data = fields.Many2one('magerp.product_attributes', 'Attribute')
    attribute = fields.Many2one('magerp.product.attribute.set', string='list')







