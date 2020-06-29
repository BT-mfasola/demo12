# -*- coding: utf-8 -*-
{
    "name": """Gantt Native PDF Advance""",
    "summary": """Added support Gantt""",
    "category": "Project",
    "images": ['static/description/banner.gif'],
    "version": "12.20.02.29.0",
    "description": """
        PDF report use pycairo for draw/
    """,
    "author": "Viktor Vorobjov",
    "license": "OPL-1",
    "website": "https://straga.github.io",
    "support": "vostraga@gmail.com",

    "depends": [
        "project",
        "project_native",
        "web_gantt_native",
    ],
    "external_dependencies": {"python": ["cairo"], "bin": []},
    "data": [

        'wizard/project_native_pdf_view.xml',
        'security/ir.model.access.csv',

    ],
    "qweb": [],
    "demo": [],

    "post_load": None,
    "pre_init_hook": None,
    "post_init_hook": None,
    "installable": True,
    "auto_install": False,
    "application": False,
}
