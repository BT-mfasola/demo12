# -*- coding: utf-8 -*-
{
    'name': 'Restrict User Login on Multi Device',
    'summary': "Restriction user to login into multi device",
    'description': "Restriction user to login into multi device",

    'author': 'iPredict IT Solutions Pvt. Ltd.',
    'website': 'http://ipredictitsolutions.com',
    'support': 'ipredictitsolutions@gmail.com',

    'category': 'Extra Tools',
    'version': '12.0.0.1.0',
    'depends': ['web'],

    'data': [
        'security/restrict_user_security.xml',
        'data/login_user_find.xml',
        'views/res_users.xml',
    ],

    'license': "OPL-1",
    'price': 20,
    'currency': "EUR",

    'auto_install': False,
    'installable': True,

    'images': ['static/description/banner.png'],
}
