# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

{
    'name': 'Customer Credit Limit',
    'version': '12.0.1.0',
    'sequence': 1,
    'category': 'Generic Modules/Accounting',
    'description':
        """
         odoo Apps will check the Customer Credit Limit on Sale order and notify to the sales manager,
        
        Customer Credit Limit, Partner Credit Limit, Credit Limit, Sale limit, Customer Credit balance, Customer credit management, Sale credit approval , Sale customer credit approval, Sale Customer Credit Informatation, Credit approval, sale approval, credit workflow , customer credit workflow,
    Customer credit limit
    Customer credit limit warning
    Check customer credit limit
    Configure customer credit limit
    How can set the customer credit limit
    How can set the customer credit limit on odoo
    How can set the customer credit limit in odoo
    Use of customer credit limit on sale order
    Change customer credit limit
    Use of customer credit limit on customer invoice
    Customer credit limit usages
    Use of customer credit limit
    Set the customer credit limit in odoo
    Set the customer credit limit with odoo
    Set the customer credit limit
    Customer credit limit odoo module
    Customer credit limit odoo app
    Customer credit limit email
    Set credit limit for customers
    Warning message to customer on crossing credit Limit
    Auto-generated email to Administrator on cutomer crossing credit limit.
    Credit limit on customer
    Credit limit for customer
    Customer credit limit setup        
    """,
    'summary': 'odoo Apps will check the Customer Credit Limit on Sale order and notify to the sales manager',
    'author': 'Devintelle Consulting Service Pvt.Ltd',
    'website': 'http://www.devintellecs.com',
    'images': ['images/main_screenshot.png'],
    'depends': ['base', 'sale_management', 'account'],
    'data': [
        'security/security.xml',
        'wizard/customer_limit_wizard_view.xml',
        'views/partner_view.xml',
        'views/sale_order_view.xml',
    ],
    'demo': [],
    'test': [],
    'css': [],
    'qweb': [],
    'js': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'price':35,
    'currency':'EUR',
    'live_test_url':'https://youtu.be/CC-a6QQcxMc',    
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
