{
    'name': 'Dashboard Financiero Completo',
    'version': '18.0.1.0.0',
    'summary': 'Dashboard completo de control financiero con gastos periódicos y cashflow avanzado',
    'description': """
    Módulo completo para control financiero empresarial:
    
    CARACTERÍSTICAS PRINCIPALES:
    Dashboard principal con KPIs financieros en tiempo real
    Control de gastos periódicos (impuestos, honorarios, servicios)
    Seguimiento individual por mes: pagado/no pagado/factura cargada
    Integración automática con facturas de proveedores y clientes desde account.move
    Cashflow avanzado con divisiones blanco/negro
    Visualización diaria, semanal, mensual
    Proyecciones vs gastos reales
    Integración completa con contabilidad de Odoo
    
    INTEGRACIÓN CON FACTURAS:
    Importa automáticamente facturas de proveedores (in_invoice, in_receipt)
    Importa automáticamente facturas de clientes (out_invoice, out_receipt)
    Estados soportados: draft, posted, paid, not_paid, partial
    Clasificación por estado de pago (payment_state)
    Proyección automática basada en fechas de vencimiento
    
    VISTAS INCLUIDAS:
    Dashboard Kanban con tarjetas informativas
    Grid view para cashflow temporal
    Listas y formularios optimizados para V18
    Gráficos interactivos de evolución
    
    REPORTES:
    Estado de caja diario/semanal/mensual
    Comparativas blanco vs negro
    Proyecciones vs realizaciones
    Análisis por proveedor y categoría
    Estado de facturas pendientes de pago
    """,
    'author': 'Biagioli Dev Team',
    'website': 'https://www.yourcompany.com',
    'category': 'Accounting/Management',
    'license': 'LGPL-3',
    'depends': [
        'account',
        'account_accountant',
        'base',
        'mail',
        'web',
    ],
    'data': [
        'data/expense_category_data.xml',
        'data/cashflow_category_data.xml', 
        'views/cashflow_minimal_views.xml', 
        'views/menu_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            # 'financial_dashboard/static/src/css/dashboard_style.scss',
            # 'financial_dashboard/static/src/js/dashboard_widgets.js',
            # 'financial_dashboard/static/src/js/cashflow_grid.js',
            # 'financial_dashboard/static/src/xml/dashboard_templates.xml',
        ],
    },
    'demo': [
        'demo/demo_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'external_dependencies': {
        'python': ['xlsxwriter'],
    },
}