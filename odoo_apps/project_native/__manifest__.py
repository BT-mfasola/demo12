# -*- coding: utf-8 -*-
{
    "name": """Gantt Native view for Projects""",
    "summary": """Added support Gantt""",
    "category": "Project",
    "images": ['static/description/banner.gif'],
    "version": "12.20.04.07.0",
    "description": """
        Gantt View for Project and Project Task
    """,
    "author": "Viktor Vorobjov",
    "license": "OPL-1",
    "website": "https://straga.github.io",
    "support": "vostraga@gmail.com",

    "depends": [
        "project",
        "hr_timesheet",
        "web_gantt_native",
        "web_widget_time_delta",
        "web_widget_colorpicker"
    ],
    "external_dependencies": {"python": [], "bin": []},
    "data": [
        'views/project_task_view.xml',
        'views/project_task_resource_view.xml',
        'views/project_task_detail_plan_view.xml',
        'views/project_calendar_access_view.xml',
        'views/resource_views.xml',
        'views/project_project_view.xml',
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
