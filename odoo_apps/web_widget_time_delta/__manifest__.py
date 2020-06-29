# -*- coding: utf-8 -*-
{
    "name": """Web Widget Time Delta""",
    "summary": """Added Time Delta Human friedly for From and List""",
    "category": "Project",
    "images": ['static/description/icon.png'],
    "version": "12.19.07.30.0",
    "description": """
    
            update: round True
            update: fix for bootstrap hide 
            
            XML string:
            For Form View - added = widget="time_delta"
            For List View - added = widget="time_delta"
            
            <field name="duration" widget="time_delta" options="{'mask_humanize_string': 'h,m',  'mask_picker_field' : ''}" />
            
            XML field:
            <field 
                    name="duration" widget="time_delta" 
                    options="{'mask_humanize_field': 'duration_scale', 'mask_picker_field' : 'duration_picker'}" 
                    class="oe_inline"
            />
            
            PYTHON
            duration = fields.Integer(string='Plan Duration') store in seconds.
            
            duration_scale = fields.Char(string='Duration Scale', related="project_id.duration_scale", readonly=True, )
            duration_picker = fields.Selection(string='Duration Picker', related="project_id.duration_picker", readonly=True, )

            
            Selection 
            @api.model
            def _get_duration_picker(self):
                value = [
                    ('day', _('Day')),
                    ('second', _('Second')),
                    ('day_second', _('Day Second'))
                ]
            return value


    """,

    "author": "Viktor Vorobjov",
    "license": "LGPL-3",
    "website": "https://straga.github.io",
    "support": "vostraga@gmail.com",
    "price": 0.00,
    "currency": "EUR",

    "depends": [
        "web"
    ],
    "external_dependencies": {"python": [], "bin": []},
    "data": [
        'view/web_widget_time_delta_view.xml'
    ],
    "qweb": [
        'static/src/xml/widget.xml',

    ],
    "demo": [],

    "post_load": None,
    "pre_init_hook": None,
    "post_init_hook": None,
    "installable": True,
    "auto_install": False,
    "application": False,
}
