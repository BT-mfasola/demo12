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

{
    "name" : "Odoo Magento 1.9 Connector",
    "version" : "1.3.0",
    "depends" : ['product','sale','delivery','base','stock','sale_stock','product_images_olbs',],
    "author" : "Globalteckz",
    "description": """
Magento e-Commerce management
Odoo 8 Magento Connector
odoo 8 magento integration
odoo magento connector
odoo magento integration
Odoo 9 Magento Connector
odoo 9 magento integration
odoo magento connector
odoo magento integration
Odoo 10 Magento Connector
odoo 10 magento integration
odoo magento connector
odoo magento integration
Odoo 11 Magento Connector
odoo 11 magento integration
odoo magento connector
odoo magento integration
Magento connector
magento integration
Magento 1.9 connector
Magento 1.8 connector
Import sales order from magento
import inventory from magento
import products from magento
import simple products from magento
import shipment from magento
import invoice from magento 
Odoo 12 Magento Connector
odoo 12 magento integration
odoo 12 magento
magento1
magento1.9
magento1.8
magento1.7
magento 1.9
magento 1.8
magento 1.7
magento 1
magento1 connector
magento1.9 connector 
magento1.8 connector 
magento1.7 connector 
magento 1.9 connector 
magento 1.8 connector 
magento 1.7 connector 
magento 1 connector
""",
    "website" : "www.globalteckz.com",
    "category" : "Sales Management",
    "price": "500.00",
    "currency": "EUR",
    'images': ['static/description/magento_connector_banner.png'],
    'summary': 'Odoo Magento 1.9 Connector will help to manage all your operations',
    "demo" : [],
    "data" : [
        'security/magento_security.xml',
        'security/ir.model.access.csv',
        'data/magento_schedular_data_view.xml',
        'views/payment_view.xml',
        'views/sale_view.xml',
        'views/product_view.xml',
        'views/magento_view.xml',
        'views/delivery_view.xml',
        'views/res_partner_view.xml',
        'data/product_data.xml',
        'views/product_images_view.xml',
        'views/invoice_view.xml',
        'views/group_customer_view.xml',
        'views/magento_log_view.xml',
        'views/stock_view.xml',
        'wizard/dashboard_wizard_view.xml',
        'views/import_order_workflow.xml',
        'views/magento_dashboard_view.xml',
        'views/magentomenu.xml',
                    ],
    'auto_install': False,
    "installable": True,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

