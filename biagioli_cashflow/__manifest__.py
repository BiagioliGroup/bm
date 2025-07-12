# -*- coding: utf-8 -*-
{
    'name': 'Biagioli Cashflow',
    'summary': "Gestión de flujo de caja y visualización de facturas proyectadas en vista Grid",
    'description': """
    Herramienta para visualizar facturas de proveedores agrupadas por fecha de vencimiento,
    con proyección de saldos y análisis financiero básico. Usa vista tipo Grid.
    """,

    'author': "Biagioli Dev Team",
    'website': "https://www.yourcompany.com",
    'category': 'Accounting',
    'version': '1.0',

    'depends': [
        'account',
        'website_sale',  # opcional
    ],

    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],

    'installable': True,
    'application': False,
    'auto_install': False,
}
