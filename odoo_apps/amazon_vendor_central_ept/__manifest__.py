{

	# App information
    'name': 'Amazon Vendor Central Integration',
    'version': '12.0',
    'category': 'Sales',
    'summary' : 'Amazon vendor central connector allows to integrate all basic operations of Amazon vendor central portal account in Odoo via EDI.',
    'license': 'OPL-1',


	# Author
    'author': 'Emipro Technologies Pvt. Ltd.',
    'website': 'http://www.emiprotechnologies.com',
    'maintainer': 'Emipro Technologies Pvt. Ltd.',

	# Dependencies
    'external_dependencies': {
        'python': [
            'asn1crypto',  # >=0.24.0
            'cryptography',  # >=2.2.2
            'nacl',  # >=1.2.0
            'paramiko',  # >=2.4.1
            'pyasn1',  # >=0.4.5
            'bcrypt',  # >=0.3.2
        ]
    },
	'depends': [
                'stock','product','purchase','sale','delivery','document','stock_picking_batch','product_expiry'
                ],

    # Views
    'data': [
            'security/res_groups.xml',
            'security/ir.model.access.csv',
            'view/actions.xml',
            'view/menu.xml',
            'wizard/view_res_config_vendor_central.xml',
            'wizard/view_res_config_ftp_server.xml',
            'wizard/view_import_product_package_info_ept.xml',
            'report/report_edi_sale_order.xml',
            'view/ir_sequence_data.xml',
            'view/view_amazon_vendor_instance.xml',
            'view/view_vendor_ftp_server.xml',
            'view/view_stock_warehouse.xml',
#             'view/view_amazon_edi_message_info.xml',
            'view/view_avc_logbook.xml',
            'view/view_sale_order.xml',
            'view/view_product.xml',
            'view/view_account_invoice.xml',
            'view/view_res_partner.xml',
            'view/view_delivery_carrier.xml',
            'view/view_stock_picking.xml',
            'view/view_stock_picking_batch.xml',
            'view/view_stock_quant.xml',
            'view/amazon_edi_ir_cron.xml',
            'view/web_templates.xml',
            'view/view_stock_move.xml',
            'view/batchwise_package_paperformatreport.xml',
            'view/view_template_batchwise_package_print.xml',
            'view/pickingwise_package_paperformat.xml',
            'view/view_template_pickingwise_package_print.xml',
            'wizard/view_stock_process_wizard.xml',
            'wizard/view_picking_to_batch_wizard.xml'
#             'view/view_amazon_sales_report_line.xml',
#             'view/view_amazon_sales_report.xml',
#             'view/view_amazon_seller_location_code.xml',
#

            ],

    # Odoo Store Specific
    'images': ['static/description/amazon-vendor-odoo-cover.jpg'],
    'installable': True,
    'live_test_url':'https://www.emiprotechnologies.com/free-trial?app=amazon-vendor-central-ept&version=12&edition=enterprise',
    'application': True,
    'auto_install': False,
    'price': '899' ,
    'currency': 'EUR',
}
