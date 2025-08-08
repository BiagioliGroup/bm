{
    'name': 'Import Interface',
    'version': '18.0.1.0.0',
    'category': 'Inventory',
    'summary': 'Interfaz flexible para importar productos desde múltiples proveedores',
    'description': '''
        Módulo para importar productos desde APIs externas:
        - Integración con WPS-inc API
        - Sistema flexible para múltiples proveedores
        - Mapeo de campos personalizable
        - Filtros de importación (solo productos con stock)
        - Cálculo de costos de importación
    ''',
    'author': 'Tu Empresa',
    'depends': ['base', 'product', 'stock', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        # 'data/supplier_data.xml',
        'views/res_partner_views.xml',
        'views/supplier_integration_views.xml',
        # 'views/product_import_views.xml',
        # 'views/import_log_views.xml',
        'views/import_products_wizard.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}