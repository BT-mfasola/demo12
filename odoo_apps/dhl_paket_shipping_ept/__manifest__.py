# -*- coding: utf-8 -*-pack
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
	 # App information
    'name': 'DHL Paket (Intraship) Odoo Shipping Connector',
    'category': 'Website',
    'version': '12.0',
    'summary': 'Odoo DHL Paket Shipping Integration helps to connect Odoo with DHL Paket and manage your Shipping operations directly from Odoo.',
	'license': 'OPL-1',
	
    # Dependencies

    'depends': ['shipping_integration_ept','stock'],

    # Views

    'data':[
        'wizard/wizard_delivery_method_report.xml',
        'views/delivery_carrier_view.xml',
        'views/view_shipping_instance_ept.xml',
        'wizard/wizard_view_send_to_ship.xml',
        'views/view_stock_picking_ept.xml',
        'views/view_company_form_ept.xml',
    ],

    # Odoo Store Specific

    'images': ['static/description/DHL-Deutsche-Post---Odoo-Connector.jpg'],

    # Author

    'author': 'Emipro Technologies Pvt. Ltd.',
    'website': 'http://www.emiprotechnologies.com',
    'maintainer': 'Emipro Technologies Pvt. Ltd.',

    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'live_test_url': 'https://www.emiprotechnologies.com/free-trial?app=dhl-paket-shipping-ept&version=12',
    'price': '149',
    'currency': 'EUR',
}
