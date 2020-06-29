# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Devintelle Software Solutions (<http://devintellecs.com>).
#
##############################################################################
{
    "name" : " Dynamic / Global Export Excel Report For all Application-xls",
    "version" : "12.0.2.0.1",
    'sequence':1,
    'category': 'Tools',
    'summary': 'odoo Apps will Export excel view for all application like: Sale, Purchase, Invoice, Picking, Hr, Project, MRP and New Custom Application',
    "depends" : ['sale','purchase','sale_stock'],
    'author': 'DevIntelle Consulting Service Pvt.Ltd',
    'website': 'http://www.devintellecs.com/',
    'images': ['images/main_screenshot.png'],
    "description": """
        odoo Apps will Export excel view for all application like: Sale, Purchase, Invoice, Picking, Hr, Project, MRP and New Custom Application
Export Excel Report For all Application
Export excel report for app application xls
Dynamic export excel report 
Global export excel report
Export excel report for all application
Grow your business using export excel report
Dynamic 	export excel report for all application
Global export excel report for all application
Export excel report
Odoo export excel report
Odoo dynamic export excel report
Odoo global export excel report
All in one export sales, purchase, invoice, inventory , customer payment , 
Sale order , purchase order lines
Invoice lines export
Import order excel odoo
Odoo Dynamic Export Excel Reports For all Application
Dynamic Global Export Excel Report for modules
Odoo Dynamic Export of Excel Reports
Odoo Dynamic Excel reports module for Odoo version 10 and version 11
Download and export anything as excel file from Odoo
Customize your own templates for the excel reports
odoo point of sale export
odoo manufacturing export
odoo accounting export
odoo journal items export 
odoo journal entries export excel
odoo sale export excel
purchase order excel export
stock inventory excel export 
all in one export excel        
    """,
    "data" : [
            'security/security.xml',
            'security/ir.model.access.csv',
            'views/dev_export_views.xml',
            'wizard/dev_export_wizard_view.xml',
#            'data/sale_order_data.xml',
#            'data/purchase_order_data.xml',
#            'data/account_invoice_data.xml',
    ],
    'installable':True,
    'application':True,
    'auto-install':False,
    'price':35.0, 
    'currency':'EUR',
    'live_test_url':'https://youtu.be/JA7q6naSmW0',  
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
