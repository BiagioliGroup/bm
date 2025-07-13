# -*- coding: utf-8 -*-
{
    'name': 'biagioli_cashflow',
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

     'assets_backend': {
        'web.assets_backend': [
            'biagioli_cashflow/static/src/css/cashflow_grid.less',
            'biagioli_cashflow/static/src/js/grid_patch.js',
        ],
    },
    
    'installable': True,
    'application': False,
    'auto_install': False,
}
