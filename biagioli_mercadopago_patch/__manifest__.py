# -*- coding: utf-8 -*-
{
    'name': 'Biagioli MercadoPago Patch',
    'version': '1.0.0',
    'depends': ['payment_mercado_pago'],
    'author': 'Sergio Biagioli',
    'category': 'Accounting/Payment Acquirers',
    'summary': 'Override MercadoPago return URL logic to force HTTPS',
    'description': """
Parche para MercadoPago que reemplaza el armado de URLs de retorno y notificación, forzando HTTPS en lugar de HTTP.
    """,
    'installable': True,
    'application': False,
    'auto_install': False,
}

