{
    'name': 'Hr manager',
    'version': '1.0.0',
    'category': 'human resources',
    'author': 'hr_saif',
    'sequence': '-100',
    'summary': 'custom_hr',
    'depends': [
        'base',
        'hr',
        'account',
        'sale_management',
        'product',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/inheritance.xml',
        'views/dynamic_field_views.xml'
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'application': True,
    'description': """
School Management System
=======================
This module extends the HR functionality to create a complete school management system.
Features include:
- Teacher management integrated with HR employees
- Student management
- Class organization
- Academic records
"""
}
