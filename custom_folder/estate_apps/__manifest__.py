# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Estate Apps',
    'version': '1.5',
    'summary': 'Estate Apps',
    'sequence': 10,
    'description': """
Estate Apps
====================
    """,
    'category': 'Estate Apps',
    'website': 'https://www.odoo.com/app/estate_apps',
    'data': [
        "security/res_groups.xml",
        "security/ir.model.access.csv",
        "views/estate_property_views.xml",
        "views/estate_settings_views.xml",
    ],
    'demo': [
        "demo/demo.xml",
    ],
    'installable': True,
    'application': True,
    'author': 'Kizaru',
    'license': 'LGPL-3',
}
