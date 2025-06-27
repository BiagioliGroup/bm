# -*- coding: utf-8 -*-
{
    'name': 'Biagioli MercadoPago Patch',
    'version': '1.0.0',
    'depends': ['payment_mercado_pago'],
    'author': 'Sergio Biagioli',
    'category': 'Accounting/Payment Acquirers',
    'summary': 'Override MercadoPago return URL logic to force HTTPS',
    'description': """

    
    Parche para los errores que Odoo tiene con MercadoPago. Ya que dejaron de desarrollar el modulo de MercadoPago, se hace necesario parcharlo para que funcione correctamente.


    """,
    'installable': True,
    'application': False,
    'auto_install': False,
    'price' : 280.00,
    'currency': 'USD',
    'license': 'GPL-3'
}

