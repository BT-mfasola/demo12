# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    # App information

    'name': 'Odoo Shipping Integration',
    'version': '12.0',
    'summary': '',
    'category': 'Sales',
    'license': 'OPL-1',

    # Dependencies

    'depends': ['delivery','product','stock_picking_batch'],
    'data':[
            'wizard/fetch_services_wizard_ept.xml',
            'wizard/wizard_shipment_report_ept.xml',
            'views/view_shipping_instance_ept.xml',
            'views/delivery_carrier_view.xml',
            'security/ir.model.access.csv',
            'report/report_template_shipping_instance_ept.xml',
            'report/report_shipping_instance_ept.xml',
            'views/res_config_setting_view.xml',
            'views/product_view.xml',
            'views/view_stock_picking_ept.xml',
            'views/sale_view.xml',
            'views/view_batch_picking_ept.xml',
            'wizard/stock_picking_to_batch_views.xml',
            'views/ir_cron.xml',
            'data/shipment_tracking_mail_template.xml',

    ],
    # Odoo Store Specific

    'images': ['static/description/Odoo-Shipping-Integration-Cover.jpg'],
    # Author
    'author': 'Emipro Technologies Pvt. Ltd.',
    'website': 'http://www.emiprotechnologies.com',
    'maintainer': 'Emipro Technologies Pvt. Ltd.',

    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False
}
