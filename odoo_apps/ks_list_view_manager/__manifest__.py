# -*- coding: utf-8 -*-
{
    'name': "List View Manager",

    'summary': """
        This app will allow app to manage the List Views on the fly and endeavour a quick and effortless way to 
        view/manage the desired data, where you’ve multifarious options to slice and dice your List View easily
        on a click.
         """,

    'description': """
	List View ,
	Advance Search ,
	Read/Edit Mode ,
	Dynamic List ,
	Hide/Show list view columns ,
	List View Manager ,
	Odoo List View ,
	Odoo Advanced Search ,
	Odoo Connector ,
	Odoo Manage List View ,
	Drag and edit columns ,
	Dynamic List View Apps , 
	Advance Dynamic Tree View ,
	Dynamic Tree View Apps ,
	Advance Tree View Apps ,
	List/Tree View Apps ,
	Tree/List View Apps  ,
	Freeze List View Header ,
	List view Advance Search ,
	Tree view Advance Search ,
	Best List View Apps ,
	Best Tree View Apps ,
	Tree View Apps ,
	List View Apps ,
	List View Management Apps ,
	Treeview ,
	Listview ,
	Tree View ,
    """,
    'author': "Ksolves India Pvt. Ltd.",
    'website': "https://www.ksolves.com/",
    'live_test_url': 'https://listview12.kappso.com/web/demo_login',
    'category': 'Tools',
    'version': '5.1.1',
    # any module necessary for this one to work correctly
    'depends': ['base', 'base_setup'],
    # always loaded
    'license': 'OPL-1',
    'currency': 'EUR',
    'price': 169.0,
    'maintainer': 'Ksolves India Pvt. Ltd.',
    'support': 'sales@ksolves.com',
    'images': ['static/description/GIF-Banner2.gif'],

    'data': [
        'views/ks_list_view_manager_assets.xml',
        'views/ks_res_config_settings.xml',
        'security/ir.model.access.csv',
        'security/ks_security_groups.xml',
    ],

    'qweb': [
        'static/src/xml/ks_list_view_manager_button.xml',
        'static/src/xml/ks_list_templates.xml',
        'static/src/xml/ks_advance_search.xml',
        'static/src/xml/ks_cancel_edit_template.xml',
    ],
    'post_init_hook': 'post_install_hook',
    'uninstall_hook': "uninstall_hook",
}
