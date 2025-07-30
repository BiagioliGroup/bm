# -*- coding: utf-8 -*-
{
    'name': 'Dux Software Integration',
    'summary': 'Integración con API de Dux Software para migración de datos',
    'description': """
        Módulo para integrar con la API de Dux Software y migrar datos hacia Odoo.
        
        Características:
        * Conexión segura con API de Dux
        * Sistema de lotes para evitar rate limiting
        * Mapeo automático de datos
        * Importación por lotes con gestión intermedia
        * Logs detallados del proceso
        * Validación de integridad de datos
        * Procesamiento en dos fases: obtención y procesamiento
    """,
    'author': 'Tu Empresa',
    'website': 'https://www.tuempresa.com',
    'category': 'Technical',
    'version': '1.1.0',
    'depends': [
        'base',
        'contacts',
        'product',
        'sale',
        'purchase',
        'account',
        'stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/import_views.xml',
        # 'views/batch_views.xml',
    ],
    'external_dependencies': {
        'python': ['requests', 'python-dateutil'],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}