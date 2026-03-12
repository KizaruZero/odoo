{
    'name': "Rental Amortization",

    'summary': "Manage rental amortization schedules",

    'description': """
Rental amortization management:
- Define rental amortization headers
- Automatically generate monthly amortization lines
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    'category': 'Rental Apps',
    'version': '19.0.1.0.0',

    'depends': ['base', 'mail', 'account', 'rental_apps'],

    'data': [
        'security/ir.model.access.csv',
        'views/view_amortization.xml',
        'views/cron.xml',
    ],

    'demo': [
        'demo/demo.xml',
    ],

    'application': True,
    'installable': True,
    'license': 'LGPL-3',
}

