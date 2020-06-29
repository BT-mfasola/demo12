# -*- coding: utf-8 -*-
{
    "name": """Gantt Native Exchange for Project""",
    "summary": """Added support Gantt""",
    "category": "Project",
    "images": ['static/description/icon.png'],
    "version": "12.20.04.02.0",
    "description": """
        FIX: load
        FIX: duration
        FIX: type
        UPDATE: constrain type
        Update: not need sort
        UPDATE: planned_hours
        ADD: stage import/export

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
    "external_dependencies": {"python": [], "bin": []},
    "data": [
        'security/security.xml',
        'wizard/project_native_exchange_view.xml',
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