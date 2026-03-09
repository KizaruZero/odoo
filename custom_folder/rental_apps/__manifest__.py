{
    'name': "rental_apps",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "Kizaru Kaede",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Rental Apps',
    'version': '0.1',
    'application': True,
    'installable': True,

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'fleet'],

    # always loaded
    'data': [
        'data/mail_template_data.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/rental_asset_request_views.xml',
        'views/rental_approval_config_views.xml',
        'wizard/rental_asset_request_reject_wizard_views.xml',
        'views/cron.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

