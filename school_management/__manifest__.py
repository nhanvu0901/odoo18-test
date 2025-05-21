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
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
