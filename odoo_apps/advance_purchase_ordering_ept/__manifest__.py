# -*- coding: utf-8 -*-
{
    # App information
    'name': 'Advance Purchase Ordering / Reordering',
    'version': '12.0',
    'category': 'stock',
    'license': 'OPL-1',
    'summary': 'Advanced reordering app for Odoo helps you to automate reordering process for your products with the help of future sales forecasting and past sales data.',
    
    
    
    # Author
    'author': 'Emipro Technologies Pvt. Ltd.',
    'maintainer': 'Emipro Technologies Pvt. Ltd.',
    'website': 'http://www.emiprotechnologies.com/',
    
    
     # Odoo Store Specific   
    'images': ['static/description/Advance-Purchase-Ordering-Reordering-Cover.jpg'],
    
    
    # Dependencies 
    'depends' : ['intercompany_transaction_ept', 'inventory_coverage_report_ept'],
    'data': [
            'security/advance_purchase_requisition_security.xml',
            'security/ir.model.access.csv',
            'data/ir_sequence.xml',
            'views/stock_warehouse_views.xml',
            'views/purchase_order_views.xml',
            'reportviews/report_requisition_process_ept_views.xml',
            'views/requisition_process_line_ept_views.xml',
            'views/requisition_summary_line_ept_views.xml',
            'views/requisition_configuration_line_ept_views.xml',
            'views/requisition_process_ept_views.xml',
            'wizardviews/advance_purhcase_ordering_config_setting_views.xml',
            'data/mail_template.xml',
            'reportviews/report_requisition_templates_ept_views.xml',
            'wizardviews/requisition_reject_reason_ept_views.xml',
            'wizardviews/export_requisition_demand_ept_views.xml',
            'views/warehouse_requisition_process_ept_views.xml',
            'views/warehouse_requisition_process_line_ept_views.xml',
            'views/warehouse_requisition_configuration_line_ept_views.xml',
            'views/warehouse_requisition_summary_line_ept_views.xml',
            'wizardviews/requisition_product_suggestion_ept_views.xml',
            'views/advance_purchase_base_menu_views.xml',
            'data/ir_config_parameter.xml'
            
    ],
    'qweb': [],
    
    # Technical
    
    'post_init_hook': 'post_init_update_rule',
    'uninstall_hook': 'uninstall_hook_update_rule',
    'installable': True,
    'auto_install': False,
    'application' : True,
    'active': False,
    'live_test_url':'https://www.emiprotechnologies.com/free-trial?app=advance-purchase-ordering-ept&version=12&edition=enterprise',
    'price': 701.00,
    'currency': 'EUR',
}
