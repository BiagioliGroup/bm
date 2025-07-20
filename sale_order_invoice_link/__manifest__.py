# -*- coding: utf-8 -*-
{
    'name':        'Sale ↔ Invoice Link',
    'version':     '1.0',
    'category':    'Sales',
    'summary':     'Relaciona pedidos de venta con sus facturas (account.move)',
    'depends': ['sale', 'account', 'repair'],
    'author':      'Sergio Biagioli[Biagioli Group]',
    'data':        [
        'views/sale_order_views.xml',
        'views/account_move_views.xml',
    ],
    'installable': True,
    'application': False,
}
