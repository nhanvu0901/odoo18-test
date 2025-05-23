{
    'name': 'school_system',
    'version': '1.0.0',
    'category': 'school',
    'author': 'hr_saif',
    'sequence': '-100',
    'summary': 'school_system',
    'depends': [
        # Base dependencies
        'base',

        # HR module - new dependency
        'hr',

        # Required for account.move (invoice) inheritance
        'account',
        # Required for sale.order inheritance
        'sale_management',  # This includes 'sale'

        # Required for product.template inheritance
        'product',
    ],
    'data': [
        'views/menu.xml',
        'security/ir.model.access.csv',
        'views/teacher_view.xml',
        'views/student_view.xml',
        'views/classe_view.xml',
        'views/wizard.xml',
        'views/inheritance.xml',
        'views/class_assigment_wizard.xml'
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
