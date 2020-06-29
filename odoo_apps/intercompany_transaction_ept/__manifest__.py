{
   
    # App information
    'name': 'Inter Company Transfer and Warehouse Transfer',
    'version': '12.0',
    'category': 'stock',
    'license': 'OPL-1',
    'summary' : 'Module to manage Inter Company Transfer and Inter Warehouse Transfer along with all required documents with easiest way by just simple configurations.',
    
         
    # Author
            
    'author': 'Emipro Technologies Pvt. Ltd.',
    'website': 'http://www.emiprotechnologies.com/',
    'maintainer': 'Emipro Technologies Pvt. Ltd.',
    
    # Dependencies 
   
    'depends': ['delivery', 'sale', 'purchase', 'stock', 'barcodes'],
    'data': [
            'data/ir_sequence.xml',
            'data/intercompany_transaction_config.xml',
            'views/inter_company_transfer_views.xml',
            'views/inter_company_transfer_config_views.xml',
            'views/rescompany_views.xml',
            'views/sale_views.xml',
            'views/purchase_views.xml',
            'views/stock_picking_views.xml',
            'views/all_search_views.xml',
            'wizard/reverse_inter_company_transfer_views.xml',
            'wizard/import_export_product_list_views.xml',
            'security/inter_company_transfer_security.xml',
            'security/ir.model.access.csv',
            'views/inter_company_transfer_process_log_views.xml'
             ],

    # Odoo Store Specific       
     'images': ['static/description/Inter-Company-Transfer-cover.png'],
              
    # Technical
    'post_init_hook': 'post_init_update_rule',
    'uninstall_hook': 'uninstall_hook_update_rule',
    'live_test_url': 'https://www.emiprotechnologies.com/free-trial?app=intercompany-transaction-ept&version=12&edition=enterprise',
    'active': True,
    'installable': True,
    'currency': 'EUR',
    'price': 149.00,
    'auto_install': False,
    'application': True,
}
