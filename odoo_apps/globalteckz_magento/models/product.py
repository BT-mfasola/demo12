
# -*- coding: utf-8 -*-
##############################################################################
#
#    Software Solutions and Services
#    Copyright (C) 2013-Today(www.globalteckz.com).                          
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from odoo import models, fields, api, _
from . PyMagento import Magento
from base64 import b64decode
import base64
import datetime
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import os
from suds.client import Client
import logging
logger = logging.getLogger('product')
# import urllib
# from urllib import urlencode
from odoo.tools.translate import _
# import sys
# reload(sys)
# sys.setdefaultencoding('utf-8')
import string 
from odoo.exceptions import UserError



class product_product(models.Model):
    _name = 'product.product'
    _inherit = 'product.product'
#
#    def copy(self, cr, uid, id, default=None, context=None):
#        if not default:
#            default = {}
#        default.update({
#            'default_code': False,
#            'images_ids': False,
#            'magento_exported': False,
#            'magento_id': False,
#        })
#        return super(product_product, self).copy(cr, uid, id, default, context=context)
#
#    def export_magento_product(self, cr, uid, ids, context=None):
#        shop_obj=self.pool.get('magento.shop')
#        if context == None:
#            context = {}
#        shop_ids = shop_obj.search(cr,uid,[('magento_shop','=',True)])
#        if len(shop_ids):
#            context['active_ids'] = ids
#            shop_obj.export_products( cr, uid, shop_ids, context)
#            shop_obj.export_images(cr, uid,shop_ids,context)
#        return True
#
#    def get_main_image(self, cr, uid, id, context=None):
#        if isinstance(id, list):
#            id = id[0]
#        images_ids = self.read(cr, uid, id, ['image_ids'], context=context)['image_ids']
#        if images_ids:
#            return images_ids[0]
#        return False
#
#    def _get_main_image(self, cr, uid, ids, field_name, arg, context=None):
#        res = {}
#        img_obj = self.pool.get('product.images')
#        for id in ids:
#            image_id = self.get_main_image(cr, uid, id, context=context)
#            if image_id:
#                image = img_obj.browse(cr, uid, image_id, context=context)
#                res[id] = image.file
#            else:
#                res[id] = False
#        return res
#            
   
    product_type = fields.Selection([('simple', 'Simple Product'),
                                         ('configurable', 'Configurable Product'),
                                         ('grouped', 'Grouped Product'),
                                         ('virtual', 'Virtual Product'),
                                         ('bundle', 'Bundle Product'),
                                         ('mygrouped', 'My Grouped'),
                                         ('downloadable', 'Downloadable Product')]
                                         , 'Type', default='simple')
    magento_id = fields.Char('Magento ID')
    wholesale_price = fields.Float('Wholesale Price')
    short_description = fields.Text('Short Description')
    news_to_date = fields.Date('To Date')
    news_from_date =  fields.Date('From Date')
    meta_title = fields.Text('Meta Title')
    meta_keyword = fields.Text('Meta Keyword')
    meta_description = fields.Text('Meta Description')
    attribute_id = fields.Many2one('magerp.product.attribute.set', 'Attribute Set')
    magento_exported = fields.Boolean('Magento Exported')
    status_type = fields.Selection([('1', 'Enabled'),
                                         ('2', 'Disabled')], 'Status', default='1')
    visibility  = fields.Selection([('1', 'Not Visible Individually'),
                                        ('2', 'Catalog'),
                                        ('3', 'Search'),
                                        ('4', 'Catalog, Search'),
                                         ], 'Visibility', default='4')
    tax_class = fields.Selection([('0', 'None'),
                                        ('2', '25% Moms'),
                                        ('4', 'Frakt')
                                         ], 'Tax Class', default='0')
    created_date =  fields.Date('Create Date')
    image_ids = fields.One2many('product.images','product_id','Product Images')
    related_prod_ids = fields.Many2many('product.product', 'related_product_rel', 'prod_id', 'name', 'ProductName', domain=[('type','!=','service')])
    upsell_prod_ids = fields.Many2many('product.product','upsell_product_rel', 'prod_id','name', 'ProductName' , domain=[('type','!=','service')])
    cross_sells_prod_ids = fields.Many2many('product.product','cross_sells_product_rel', 'prod_id','name', 'Product Name', domain=[('type','!=','service')])
    shop_prod_ids = fields.Many2many('magento.shop','sale_shop_rel', 'prod_id','name', 'Shop Name', domain=[('magento_shop','=',True)]),
    category_ids = fields.One2many('product.multi.category','product_id','Product Categories')
    prods_cat_id = fields.One2many('product.multi.category', 'product_id','Catergories')
    associated_prod_ids = fields.One2many('associated.products','product_id','Associated Products')
    bundle_prod_ids = fields.One2many('bundle.products','product_id','Bundle Products')
    tier_price_ids = fields.One2many('products.tier.price','product_id','Tier Price')
    mygrouped_prod_ids = fields.One2many('mygrouped.products','product_id','My Grouped Products')
    input_type = fields.Selection([('drop-down', 'Drop-down'),('radiobuttons', 'Radio Buttons'),('checkbox', 'Checkbox'),('multipleselect', 'Multiple Select')],'Input Type')
    is_required = fields.Selection([('yes', 'Yes'),('no', 'No')],'Is Required')
    top_position = fields.Char('Position', size=100)
    special_price =  fields.Float('Special Price')
    special_price_from_date = fields.Datetime('Special Price From Date')
    special_price_to_date = fields.Datetime('Special Price To Date')
    select_instance = fields.Many2one('magento.instance','Magento Instance')
    shop_prod_ids = fields.Many2many('magento.shop','sale_shop_rel', 'prod_id','name', 'Shop Name', domain=[('magento_shop','=',True)])
    mag_color = fields.Many2one('magerp.product_attribute_options','Select Color')
    mag_size = fields.Many2one('magerp.product_attribute_options','Select Size')
    magento_attribute = fields.One2many('product.attribute.detail', 'magento_product', 'Attributes')
    mag_description=fields.Text(string='Long Description')
    mag_short_description = fields.Text(string='Short Description')
    color = fields.Char(string='Color')


#     _defaults = {
#         'status_type':'1',
#         'visibility':'4',
#         'tax_class':'0',
#         'product_type':'simple',
#         'created_date':fields.datetime.now(),
#     }

##    def create(self, cr, uid, vals, context=None):
##        if context is None:
##            context = {}
##        ctx = dict(context or {}, create_product_product=True)
##        if vals.get('upc_barcode') :
##            barcode = vals.get('upc_barcode')
##            vals['magento_attribute.attribute_color'] = 'att_upc'
##            vals['magento_attribute.attribute_size'] = barcode
##        return super(product_product, self).create(cr, uid, vals, context=ctx)
#
#    def get_available_qty(self,cr,uid,ids):
#        logger.error('ids %s', ids)
#        (data,) = self.browse(cr,uid,ids)
#        return data.qty_available
#

    @api.multi
    def create_products(self,product_list,instances,log_id):
        print ('working+++++++')
        att_set_obj=self.env['magerp.product.attribute.set']
        prod_cat_obj=self.env['product.category']
        shop_obj=self.env['magento.shop']
        prod_obj=self.env['product.product']
        magento_log_line = self.env['magento.log.details']
        attribute_obj =self.env['magerp.product_attributes']
        product_attribute_obj=self.env['magerp.product_attribute_options']
        attribute_detail = self.env['product.attribute.detail']
        shop_id=shop_obj.search([('magento_instance_id','=',instances.id)])
        if not shop_id:
            raise  UserError(_('Error'), _('Please, create the shop first'))
        newProductData={}
        mage = Magento(instances.location, instances.apiusername, instances.apipassoword)
        mage.connect()
        for each_prod in product_list:
            print("each_prod",each_prod)
#             try:
            prod_id_magento=int(each_prod['product_id'])
            att_obj= mage.client.factory.create('catalogProductRequestAttributes')
            att_ids=att_set_obj.search([('code','=',each_prod['set'])])
            print("att_ids",att_ids.code)
            attribute_list = []
            att_id=[]
            if att_ids :
                for attributes in att_ids.attribute_line_id:
                    attribute_list.append(str(attributes.attribute_id_data.attribute_code))
                print("attribute_lis,",attribute_list)
            att_obj.additional_attributes=attribute_list
#                 print"attribute_list",att_obj.additional_attributes
            product_info = mage.client.service.catalogProductInfo(mage.token,prod_id_magento,None,att_obj)
            print ('product_info++++++++++',product_info)
            cat_id = []
            additional=product_info['additional_attributes'] if hasattr(product_info ,'additional_attributes') else False
            prods=prod_obj.search([('default_code','=',each_prod['sku']),('active','=',True)])
            if each_prod['category_ids']:
                if not prods:
                    for categ_id in each_prod['category_ids']:
                        cat = prod_cat_obj.search([('magento_id','=',categ_id)])
                        if cat:
                            cat_id.append((0,0,{'name':cat[0].id}))
            if att_ids:
                att_id=att_ids[0].id
            if hasattr(product_info ,'weight'):
                product_weight=product_info['weight']
                prod_weight_string = str(product_weight)
                if ',' in prod_weight_string:
                    product_weight_string = string.replace(prod_weight_string, ',', '.')
                    product_weight = float(product_weight_string)
            else:
                product_weight=0.00
            
            special_price = ''
            special_from_date = ''
            special_to_date = ''
            meta_title = ''
            meta_keyword = ''
            meta_description = ''
            description=''
            short_description=''
            price = 0.00
            
            if hasattr(product_info ,'additional_attributes'):
                for attribute in product_info['additional_attributes']:
                    if attribute['key'] == 'special_price':
                        special_price = attribute['value']
                         
                    if attribute['key'] == 'special_from_date':
                        special_from_date = attribute['value']
                         
                    if attribute['key'] == 'special_to_date':
                        special_to_date = attribute['value']
                        
                    if attribute['key'] == 'meta_title':
                        meta_title = attribute['value']
                        
                    if attribute['key'] == 'meta_keyword':
                        meta_keyword = attribute['value']
                        
                    if attribute['key'] == 'meta_description':
                        meta_description = attribute['value']
                        
                    if attribute['key'] == 'description':
                        description = attribute['value']
                        
                    if attribute['key'] == 'short_description':
                        short_description = attribute['value']
                        
                    if attribute['key'] == 'price':
                        price = attribute['value']
                        
            newProductData = {
                'name':each_prod['name'] and each_prod['name'][:128].strip(" "),
                'prods_cat_id' :cat_id ,
                'type' : 'product',
                'mag_description':description or '',
                'mag_short_description':short_description or '',
                'default_code':each_prod['sku'],
                'lst_price': price or 0.00,
                'product_type':each_prod['type'],
                'magento_id':each_prod['product_id'].strip(" "),
                'attribute_id':att_id,
                'magento_exported':True,
                'weight':float(product_weight),
                'visibility':product_info['visibility'] if hasattr(product_info ,'visibility') else False,
                'product_type': each_prod['type'],
                'status_type':product_info['status'] if hasattr(product_info ,'status') else False,
                'special_price':special_price or 0.0,
                'special_price_from_date':special_from_date or False,
                'special_price_to_date':special_to_date or False,
                'meta_title':meta_title or '',
                'meta_keyword':meta_keyword or '',
                'meta_description':meta_description or '',
                'select_instance': instances.id,
            }
            print("newProductData",newProductData)
            prod_temp_id=prod_obj.search([('default_code','=',each_prod['sku']),('active','=',True)])
            line=[]
            if hasattr(product_info ,'additional_attributes'):
                additional=product_info['additional_attributes']
                for attribute in additional:
                    if attribute['value'] != None:
                        if not len(prod_temp_id):
                            if not len(prod_temp_id.magento_attribute):
                                produt_id = product_attribute_obj.search([('attribute_name','=',attribute['key']),('value','=',attribute['value'])])
                                if produt_id:
                                    for product_ids in produt_id:
                                        line.append((0,0,{'market_pl':product_ids.attribute_id.id,'market_ch':product_ids.id}))
                                else:
                                    attribute_id=attribute_obj.search([('attribute_code','=',attribute['key'])])
                                    if attribute_id:
                                        attribute_opt_id = self.env['magerp.product_attribute_options'].search([('attribute_id','=',attribute_id[0].id),('value','=',attribute['value'])])
                                        if attribute_opt_id:
                                            attribute_opt_ids = attribute_opt_id[0]
                                        if not attribute_opt_id:
                                            attribute_opt_ids = self.env['magerp.product_attribute_options'].create({'attribute_id':attribute_id[0].id,'value':attribute['value']})
                                        line.append((0,0,{'market_pl':attribute_id[0].id,'market_ch':attribute_opt_ids.id}))
                            else:
                                mage_prod_detail = self.env['product.attribute.detail']
                                mage_options_id = mage_prod_detail.search([('market_pl','=',attribute['key']),('magento_product','=',prod_temp_id.id)])
                                if mage_options_id:
                                    value = {'market_ch':attribute['value']}
                                    mage_options_id.write(value)
                                else:
                                    prod_detail = mage_options_id.create({'magento_product':prod_temp_id.id,'market_pl':attribute['key'],'market_ch':attribute['value']})
                newProductData['magento_attribute']=line
            if not prod_temp_id:
                prod_id=prod_obj.create(newProductData)
                print ('prod_id++++++++++',prod_id)
                self._cr.commit()
            else:
                prod_temp_id.write(newProductData)
            self._cr.commit()
#             except Exception, exc:
#                 logger.error('Exception===================:  %s', exc)
#                 magento_log_line.create({'name':'Import Product','description':exc,'create_date':date.today(),
#                                           'magento_log_id':log_id.id})
#                 log_id.write({'description': 'Something went wrong'}) 
#                 pass   
        return True
#
#
#
    @api.one
    def export_single_product(self):
        prod_data = self
        image_obj=self.pool.get('product.images')
        if not prod_data.select_instance:
            raise  UserError(_('Error'), _('Please Select Magento Instance'))
        (shop_data,) = prod_data.select_instance
        mage = Magento(shop_data.location,shop_data.apiusername,shop_data.apipassoword)
        mage.connect()
        attribute = mage.client.factory.create('catalogProductReturnEntity')
        product_Data={}
        if not prod_data.default_code:
            raise  UserError(_('Error'), _('Please Enter SKU'))
        if not prod_data.attribute_id:
            raise  UserError(_('Error'), _('Please Enter Attribute SET'))
        attribute = mage.client.factory.create('catalogProductAdditionalAttributesEntity')       
        attributes=[]
        for atts in prod_data.magento_attribute:
            if atts.market_pl.attribute_code=='name':
                continue
            if atts.market_pl.attribute_code=='description':
                continue
            if atts.market_pl.attribute_code=='short_dexcription':
                continue
            if atts.market_pl.attribute_code=='price':
                continue
            if atts.market_pl.attribute_code=='meta_title':
                continue
            if atts.market_pl.attribute_code=='meta_keyword':
                continue
            if atts.market_pl.attribute_code=='meta_description':
                continue
            attributes.append({'key': atts.market_pl.attribute_code, 'value': atts.market_ch.value })
        if attributes:
               attribute['single_data'] = [attributes]
        if prod_data.product_type == 'simple':
            sku=prod_data.default_code
            type=prod_data.product_type or 'simple'
            set=prod_data.attribute_id.code
            id = prod_data.magento_id
            websites_list= []
            if len(prod_data.shop_prod_ids):
                for each_shop in prod_data.shop_prod_ids:
                    if each_shop.store_id:
                        websites_list.append(str(each_shop.store_id))
            if prod_data.special_price and prod_data.special_price_from_date and prod_data.special_price_to_date:
                product_Data={
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
            else:
                product_Data={
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
            if len(prod_data.prods_cat_id):
                product_Data['categories'] = []
                for each_categ in prod_data.prods_cat_id:
                    if each_categ.name.magento_id:
                        product_Data['categories'].append(each_categ.name.magento_id)
            try:
                if not prod_data.magento_exported:
                    list_prods = mage.client.service.catalogProductCreate(mage.token,type,set,sku,product_Data)
                    prod_data.write({'magento_exported':True,'magento_id':list_prods})
                else:
                    list_prods = mage.client.service.catalogProductUpdate(mage.token,prod_data.magento_id,product_Data,0,'ID')
                    logger.error('---------simple----------list_prods %s', list_prods)
            except Exception as exc:
                logger.error('exc %s', exc)
                prod_data.write({'is_faulty':True,'faulty_log':str(exc)})
                self._cr.commit()
            in_stock = 0
            manage_stock = 0
            if int(prod_data.qty_available) >= 1:
                in_stock = 1
                manage_stock = 1
            try:
                sku_list = {'qty':prod_data.qty_available,'is_in_stock':in_stock,'manage_stock':manage_stock}
                mage.client.service.catalogInventoryStockItemUpdate(mage.token,prod_data.default_code,sku_list)
            except:
                pass
            image_id = prod_data.image_ids
            for image_data in image_id:
                if image_data.link== True:
                    file_contain = urllib.urlopen(image_data.url).read()
                    image_path = base64.encodestring(file_contain)
                    image='image/jpeg'
                else:
                    image_path = image_data.file_db_store
                    image='image/jpeg'
                file={
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
                data={
                    'label': image_data.name,
                    'position':image_data.position,
                    'types':image_type,
                    'exclude':'0',
                    'file':file,
                    'remove':'0'
                }
                try:
                    if not image_data.is_exported:
                        img = mage.client.service.catalogProductAttributeMediaCreate(mage.token,prod_data.default_code,data,0,'sku')
                        if img:
                            image_data.write({'image_name_mag':img})
                    else:
                        file = image_data.image_name_mag
                        mage.client.service.catalogProductAttributeMediaUpdate(mage.token,prod_data.default_code,file,data,0,'sku')
                    image_data.write({'is_exported':True})
                except:
                    pass

        if prod_data.product_type == 'configurable':
            websites_list= []
            if len(prod_data.shop_prod_ids):
                for each_shop in prod_data.shop_prod_ids:
                    if each_shop.store_id:
                        websites_list.append(str(each_shop.store_id))
                    else:
                        raise osv.except_osv(_('Error'), _('Store id not found for %s' % (each_shop.name)))

            if prod_data.associated_prod_ids:
                for assc_id in prod_data.associated_prod_ids:
                    for data in assc_id.name:
                        attributes = []
                        attribute = mage.client.factory.create('associativeArray')
                        attribute = mage.client.factory.create('catalogProductAdditionalAttributesEntity')
                        for attr in prod_data.magento_attribute:
                            if attr.attribute_size:
                                val = attr.attribute_size.label
                            attributes.append({'key': attr.attribute_color.attribute_code, 'value': val})
                            if attr.attribute_color.attribute_code != 'att_upc':
                                attributes.append({'key': 'att_upc', 'value': prod_data.upc_barcode or ''})
                        if attributes:
                            attribute['single_data'] = [attributes]
                        sku =data.default_code
                        type=data.product_type or 'simple'
                        set=data.attribute_id.code
                        product_Data={
                            'name':data.name,
                            'description':data.mag_description or '',
                            'short_description':data.mag_short_description or '',
                            'price':data.list_price,
                            'categories':[str(data.categ_id.magento_id)],
                            'status':data.status_type or 1,
                            'weight':data.weight,
                            'visibility':data.visibility or 4,
                            'meta_title':data.meta_title[:225] if prod_data.meta_title else '',
                            'meta_keyword':data.meta_keyword[:225] if prod_data.meta_keyword else '',
                            'meta_description':data.meta_description[:225] if prod_data.meta_description else '',
                            'special_price':prod_data.special_price or 0.0,
                            'special_from_date':prod_data.special_price_from_date or False,
                            'special_to_date':prod_data.special_price_to_date or False,
                            'websites' : websites_list,
                            'additional_attributes':attributes,
                            'visibility':1,
                            'tax_class_id' : prod_data.tax_class or '',
                        }
                        try:
                            if not data.magento_exported:
                                list_prods = mage.client.service.catalogProductCreate(mage.token,type,set,sku,product_Data)
                                
                            else:
                                list_prods = mage.client.service.catalogProductUpdate(mage.token,sku,product_Data)
                                logger.error('---------simple----------list_prods %s', list_prods)
                        except Exception as exc:
                            logger.error('exc %s', exc)
                            data.write({'is_faulty':True,'magento_exported':True, 'faulty_log':str(exc)})
                            self._cr.commit()
                        
            sku=prod_data.default_code
            type=prod_data.product_type or 'simple'
            set=prod_data.attribute_id.code
            attributes = []
            attribute = mage.client.factory.create('associativeArray')
            attribute = mage.client.factory.create('catalogProductAdditionalAttributesEntity')
            for attr in prod_data.magento_attribute:
                if attr.market_ch:
                    val = attr.market_ch.label
                attributes.append({'key': attr.market_pl.attribute_code, 'value': val})
                if attr.market_pl.attribute_code != 'att_upc':
                    attributes.append({'key': 'att_upc', 'value': prod_data.upc_barcode or ''})
            if attributes:
                attribute['single_data'] = [attributes]

            
            product_Data={
                'name':prod_data.name,
                'description':prod_data.mag_description or '',
                'short_description':prod_data.mag_short_description or '',
                'price':prod_data.list_price,
                'categories':[str(prod_data.categ_id.magento_id)],
                'status':prod_data.status_type or 1,
                'weight':prod_data.weight,
                'visibility':prod_data.visibility or 4,
                'meta_title':prod_data.meta_title[:225] if prod_data.meta_title else '',
                'meta_keyword':prod_data.meta_keyword[:225] if prod_data.meta_keyword else '',
                'meta_description':prod_data.meta_description[:225] if prod_data.meta_description else '',
                'websites' : websites_list,
                'additional_attributes':attributes,
                'tax_class_id' : prod_data.tax_class or '',
            }
            associated_skus =[]
            if prod_data.associated_prod_ids:
                for associated_data in prod_data.associated_prod_ids:
                    associated_skus.append(associated_data.name.default_code)
                product_Data['associated_skus']=associated_skus
            try:
                if not prod_data.magento_exported:
                    list_prods = mage.client.service.catalogProductCreate(mage.token,type,set,sku,product_Data)
                else:
                    list_prods = mage.client.service.catalogProductUpdate(mage.token,sku,product_Data)
                    logger.error('---------simple----------list_prods %s', list_prods)
                prod_data.write({'magento_exported':True,'magento_id':list_prods,'is_faulty':False,'faulty_log':False})
            except Exception as exc:
                logger.error('exc %s', exc)
                prod_data.write({'is_faulty':True,'faulty_log':str(exc)})
                self._cr.commit()

        return True
#    
#    def export_single_stock(self, cr, uid, ids, context):
#        prod_data = self.browse(cr , uid , ids , context)
#        if not prod_data.shop_prod_ids:
#            raise osv.except_osv(_('Error'), _('Please Enter SKU for %s' % (prod_data.shop_prod_ids)))
#        (shop_data,) = prod_data.shop_prod_ids[0]
#        mage = Magento(shop_data.magento_instance_id.location,shop_data.magento_instance_id.apiusername,shop_data.magento_instance_id.apipassoword)
#        mage.connect()
#        in_stock = 0
#        manage_stock = 0
#        if int(prod_data.qty_available) >= 1:
#            in_stock = 1
#            manage_stock = 1
#        try:
#            sku_list = {'qty':prod_data.qty_available,'is_in_stock':in_stock,'manage_stock':manage_stock}
#            mage.client.service.catalogInventoryStockItemUpdate(mage.token,prod_data.default_code,sku_list)
#        except:
#            pass
#    
#        return True
#
#    def export_single_link_products(self, cr, uid, ids, context):
##       Update Related Products, Up-sell Products, Cross-sell Products To Magento Products
#        related_prod_skus =[]
#        upsell_prod_skus =[]
#        cross_sells_prod_skus =[]
#        prod_data = self.browse(cr , uid , ids , context)
#        (shop_data,) = prod_data.shop_prod_ids[0]
#        mage = Magento(shop_data.magento_instance_id.location,shop_data.magento_instance_id.apiusername,shop_data.magento_instance_id.apipassoword)
#        mage.connect()
#        if prod_data.magento_exported:
#            if not prod_data.default_code:
#                raise osv.except_osv(_('Error'), _('Please Enter SKU for %s' % (prod_data.name)))
#            if not prod_data.attribute_id:
#                raise osv.except_osv(_('Error'), _('Please Enter Attribute SET for %s' % (prod_data.name)))
#            sku=prod_data.default_code
#            set=prod_data.attribute_id.code
#
#            if prod_data.related_prod_ids:
#                for related_prod_id in prod_data.related_prod_ids:
#                    if related_prod_id.default_code:
#                        if related_prod_id.magento_exported:
#                            data ={ 'position':0, 'qty':1 }
#                            related_prod_sku = related_prod_id.default_code
#                            list_prods = mage.client.service.catalogProductLinkAssign(mage.token,'related',sku,related_prod_sku,data,'sku')
#                        else:
#                            raise osv.except_osv(_('Error'), _('Related SKU %s not in Magento' % (related_prod_id.default_code)))
#
#            if prod_data.upsell_prod_ids:
#                for upsell_prod_id in prod_data.upsell_prod_ids:
#                    if upsell_prod_id.default_code:
#                        if upsell_prod_id.magento_exported:
#                            data ={ 'position':0, 'qty':1 }
#                            upsell_prod_sku = upsell_prod_id.default_code
#                            list_prods = mage.client.service.catalogProductLinkAssign(mage.token,'up_sell',sku,upsell_prod_sku,data,'sku')
#                        else:
#                            raise osv.except_osv(_('Error'), _('Upsell SKU %s not in Magento' % (upsell_prod_id.default_code)))
#            if prod_data.cross_sells_prod_ids:
#                for cross_sells_prod_id in prod_data.cross_sells_prod_ids:
#                    if cross_sells_prod_id.default_code:
#                        if cross_sells_prod_id.magento_exported:
#                            data ={ 'position':0, 'qty':1 }
#                            cross_sells_prod_sku = cross_sells_prod_id.default_code
#                            list_prods = mage.client.service.catalogProductLinkAssign(mage.token,'cross_sell',sku,cross_sells_prod_sku,data,'sku')
#                        else:
#                            raise osv.except_osv(_('Error'), _('Cross sell SKU %s not in Magento' % (cross_sells_prod_id.default_code)))
#        return True
#
#
#    def createMultiCategory(self,cr,uid,shop_id,prod_id,category_ids):
#        prod_multi_cat_obj=self.pool.get('product.multi.category')
#        prod_cat_obj=self.pool.get('product.category')
#        for each_category in category_ids:
#            cat_ids=prod_cat_obj.search(cr,uid,[('magento_id','=',each_category),('shop_id','=',shop_id[0])])
#            if cat_ids:
#                product_cat_ids = prod_multi_cat_obj.search(cr,uid,[('product_id','=',prod_id),('name','=',cat_ids[0])])
#                if not len(product_cat_ids):
#                    prod_multi_cat_obj.create(cr,uid,{'product_id':prod_id,'name':cat_ids[0]})
#        
#product_product()
#
class product_multi_category(models.Model):
    _name = 'product.multi.category'
    
    product_id = fields.Many2one('product.product','Product')
    name = fields.Many2one('product.category','Category')
 
product_multi_category()

class associated_products(models.Model):
    _name = 'associated.products'
 
    product_id = fields.Many2one('product.product','Product')
    name = fields.Many2one('product.product','Product')
    
associated_products()

class bundle_products(models.Model):
    _name = 'bundle.products'
   
    product_id = fields.Many2one('product.product','Product')
    name = fields.Many2one('product.product','Product')
    default_qty = fields.Integer('Default Qty')
    user_defined_qty = fields.Selection([('yes', 'Yes'),('no', 'No')], 'User Defined Qty')
    position = fields.Char('Position', size=100)
    default = fields.Boolean('Default')
       
    
bundle_products()

class products_tier_price(models.Model):
    _name = 'products.tier.price'
   
    product_id = fields.Many2one('product.product','Product')
    shop_id = fields.Many2one('magento.shop','Website')
    group_id = fields.Many2one('customer.group','Customer Group')
    quantity = fields.Integer('Quantity')
    tier_price = fields.Float('Price')

  
products_tier_price()

class mygrouped_products(models.Model):
    _name = 'mygrouped.products'
    
    product_id = fields.Many2one('product.product','Product')
    name = fields.Many2one('product.product','Product')
        

mygrouped_products()

class product_attribute_detail(models.Model):
    _name = 'product.attribute.detail'

    magento_product = fields.Many2one('product.product', 'Product')
    market_pl = fields.Many2one('magerp.product_attributes','Attribute')
    market_ch = fields.Many2one('magerp.product_attribute_options','Attribute Options')
    
product_attribute_detail()

class product_category(models.Model):
    _inherit = 'product.category'
  
    magento_id = fields.Integer('Code')
    shop_id = fields.Many2one('magento.shop','shop')
    instance_id = fields.Many2one('magento.instance', string='Magento Instance')
   
    @api.multi
    def create_cat(self,local_prod,mag,name,log_id):
        magento_log_line = self.env['magento.log.details']
        try:
            if hasattr(local_prod ,'name'):
                if local_prod['parent_id']== "0":
                    search_name=str(local_prod['name'])
                    cat_parent={
                        'name':str(local_prod['name']),'parent_id':False,'magento_id':int(local_prod['category_id']),'instance_id':name.id
                    }
                    cate_id=self.search([('name','=',search_name),('instance_id','=',name.id)])
                    if cate_id:
                        cate_id=cate_id.write(cat_parent)
                    else:
                        cate_id=self.create(cat_parent)
                else:
                    cat_cat_child={}
                    cat_child_id=self.search([('magento_id','=',int(local_prod['parent_id'])),('instance_id','=',name.id)])
                    if cat_child_id:
                        for data in cat_child_id:
                            cat_cat_child={
                                'name':str(local_prod['name']),'parent_id':data.id,'magento_id':int(local_prod['category_id']),'instance_id':name.id
                            }
                            sub_child_id=self.search([('magento_id','=',local_prod['category_id'])])
                            if sub_child_id:
                               cate_id=sub_child_id.write(cat_cat_child)
                            else:
                                print('categ+++++++++++',self.create(cat_cat_child))

                    else:
                        cat_cat_child_new={}
                        cat_cat_child_new={
                                'name':str(local_prod['name']),'parent_id':int(local_prod['parent_id']),'magento_id':int(local_prod['category_id']),'instance_id':name.id
                        }
                        sub_sub_child_id=self.search([('magento_id','=',int(local_prod['category_id']))])
                        if sub_sub_child_id:
                            cate_id=sub_sub_child_id.write(cat_cat_child_new)
                        else:
                            print ('categ+++++++++++',self.create(cat_cat_child_new))

                self._cr.commit()
        except Exception as exc:
            logger.error('Exception===================:  %s', exc)
            magento_log_line.create({'name':'Create Category','description':exc,'create_date':date.today(),
                                      'magento_log_id':log_id.id})
            log_id.write({'description': 'Something went wrong'}) 
            pass
        return True

product_category()

