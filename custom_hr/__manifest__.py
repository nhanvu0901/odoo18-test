# -*- coding: utf-8 -*-
{
    'name': "Custom HR - Dynamic Fields",

    'summary': "Create dynamic fields for HR Employee forms",

    'description': """
        This module allows HR managers to dynamically create custom fields 
        for employee forms without requiring technical knowledge.
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    'category': 'Human Resources',
    'version': '18.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/wizard.xml',
        'views/hr_employee_views.xml',
        'views/res_config_settings.xml',
    ],

    'installable': True,
    'application': False,
    'auto_install': False,
}
