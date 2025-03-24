# -*- coding: utf-8 -*-
{
    'name': "viumi-payment",

    'summary': "Modulo de integracion para pasarela de pagos VIUMI. En Argentina, VIUMI es una pasarela desarrollada por Banco Macro. Powered by BiagioliGroup",

    'description': """
Long description of module's purpose
    """,

    'author': "BIagioliGroup",
    'website': "https://www.biagioligroup.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting/Payment Acquirers',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['payment'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'data/payment_provider_data.xml',  # 👈 agregalo aquí

    ],
    'assets' : {},
    'installable' : True,
    'application' : False,
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

