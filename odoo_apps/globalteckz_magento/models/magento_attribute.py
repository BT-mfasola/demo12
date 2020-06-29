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
from PyMagento import Magento
from base64 import b64decode
import base64
import datetime
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import os
from suds.client import Client
import logging
logger = logging.getLogger('product')
from urllib import urlencode
from odoo.tools.translate import _

class product_product(models.Model):
    _name = 'product.product'
    _inherit = 'product.product'


#    def create_products(self,cr,uid,product_list,instances,context):
#        att_set_obj=self.pool.get('magerp.product.attribute.set')
#        prod_cat_obj=self.pool.get('product.category')
#        shop_obj=self.pool.get('magento.shop')
#        shop_id=shop_obj.search(cr,uid,[('magento_instance_id','=',instances.id)])
#        if not shop_id:
#            raise osv.except_osv(_('Error'), _('Please, create the shop first'))
#        newProductData={}
#        mage = Magento(instances.location, instances.apiusername, instances.apipassoword)
#        mage.connect()
#        for each_prod in product_list:
#            prod_id_magento=int(each_prod['product_id'])
#            try:
#                att_obj=mage.client.factory.create('catalogProductRequestAttributes')
#                att_obj.additional_attributes=['att_asin','att_ean','att_itemno','config_size_mysleevedesign','att_producerid']
#                product_info  = mage.client.service.catalogProductInfo(mage.token,prod_id_magento,None,att_obj)
#                additional=product_info['additional_attributes']
#                size ,producerid, itemno ,ean, asin="","","","",""
#                for attribute in additional:
#                    if attribute['key']=='att_asin':
#                        if attribute['value']:
#                            asin=attribute['value']
#                        continue
#                    elif attribute['key']=='att_ean':
#                        if attribute['value'].strip():
#                            ean=attribute['value']
#                        continue
#                    elif attribute['key']=='att_itemno':
#                        itemno=attribute['value']
#                        continue
#                    elif attribute['key']=='config_size_mysleevedesign':
#                        size=attribute['value']
#                        continue
#                    elif attribute['key']=='att_producerid':
#                        producerid=attribute['value']
#                        continue 
#
#               
#            except Exception, exc:
#                pass
#
#            cat_id = 1
#            if each_prod['category_ids']:
#                cat_ids=prod_cat_obj.search(cr,uid,[('magento_id','=',each_prod['category_ids'][0]),('shop_id','=',shop_id[0])])
#                if cat_ids:
#                    cat_id = cat_ids[0]
#                else:
#                    cat_id = 1
#
#            att_ids=att_set_obj.search(cr,uid,[('code','=',each_prod['set'])])
#            if att_ids:
#                att_id=att_ids[0]
#            else:
#                att_id=False
#
#            if hasattr(product_info ,'short_description') and product_info['short_description'] != None:
#                description=product_info['short_description'].encode('utf-8', 'ignore')
#            elif hasattr(product_info ,'description') and product_info['description'] != None:
#                description=product_info['description'].encode('utf-8', 'ignore')
#            else:
#                description=False
#
#            if hasattr(product_info ,'price'):
#                price=product_info['price']
#            else:
#                price=1.00
#
#            if hasattr(product_info ,'weight'):
#                product_weight=product_info['weight']
#            else:
#                product_weight=0.00
#            newProductData = {
#                    'name':each_prod['name'][:128].encode('utf-8').strip(" "),
#                    'categ_id' :cat_id ,
#                    'type' : 'product',
#                    'description':description,
#                    'description_sale':description,
#                    'description_purchase':description,
#                    'short_description':description,
#                    'name_template' : each_prod['name'][:128].encode('utf-8').strip(" "),
#                    'default_code':each_prod['sku'],
#                    'list_price': price,
#                    'product_type':each_prod['type'],
#                    'magento_id':each_prod['product_id'].strip(" "),
#                    'attribute_id':att_id,
#                    'magento_exported':True,
#                    'weight':product_weight,
#                    'visibility':product_info['visibility'],
#                    'tax_class':product_info['tax_class_id']if hasattr(product_info ,'tax_class_id') else False,
#                    'product_type':each_prod['type'],
#                    'status_type':product_info['status'] if hasattr(product_info ,'status') else False,
#                    'meta_title':each_prod['meta_title'] if hasattr(each_prod ,'meta_title') else False,
#                    'meta_keyword':each_prod['meta_keyword'] if hasattr(each_prod ,'meta_keyword') else False,
#                    'meta_description':each_prod['meta_description'] if hasattr(each_prod ,'meta_description') else False,
#                    'asin':asin,
#                    'item_no':itemno,
#                    'size':size,
#                    'ean13':ean,
#                    'producer_id':producerid
#                    
#            }
#            prod_temp_id=self.search(cr,uid,[('default_code','=',each_prod['sku']),('active','=',True)])
#            if not prod_temp_id:
#                prod_id=self.create(cr,uid,newProductData)
#            else:
#                self.write(cr,uid,prod_temp_id,newProductData)
#                prod_id = prod_temp_id[0]
#
#            self.createMultiCategory(cr,uid,shop_id,prod_id,each_prod['category_ids'])
#            logger.error('prod_id %s', prod_id)
#            cr.commit()
#        return True