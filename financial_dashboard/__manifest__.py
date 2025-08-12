{
    'name': 'Dashboard Financiero Completo',
    'version': '18.0.1.0.0',
    'summary': 'Dashboard completo de control financiero con gastos periódicos y cashflow avanzado',
    'description': """
    Módulo completo para control financiero empresarial:
    
    CARACTERÍSTICAS PRINCIPALES:
    • Dashboard principal con KPIs financieros en tiempo real
    • Control de gastos periódicos (impuestos, honorarios, servicios)
    • Seguimiento individual por mes: pagado/no pagado/factura cargada
    • Integración automática con facturas de proveedores y clientes desde account.move
    • Cashflow avanzado con divisiones blanco/negro
    • Visualización diaria, semanal, mensual
    • Proyecciones vs gastos reales
    • Integración completa con contabilidad de Odoo
    
    INTEGRACIÓN CON FACTURAS:
    • Importa automáticamente facturas de proveedores (in_invoice, in_receipt)
    • Importa automáticamente facturas de clientes (out_invoice, out_receipt)
    • Estados soportados: draft, posted, paid, not_paid, partial
    • Clasificación por estado de pago (payment_state)
    • Proyección automática basada en fechas de vencimiento
    
    VISTAS INCLUIDAS:
    • Dashboard Kanban con tarjetas informativas
    • Grid view para cashflow temporal
    • Listas y formularios optimizados para V18
    • Gráficos interactivos de evolución
    
    REPORTES:
    • Estado de caja diario/semanal/mensual
    • Comparativas blanco vs negro
    • Proyecciones vs realizaciones
    • Análisis por proveedor y categoría
    • Estado de facturas pendientes de pago
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
        # ========================================== #
        # PASO 1: SEGURIDAD BÁSICA (solo grupos)
        # ========================================== #
        'security/security.xml',
        
        # ========================================== #
        # PASO 2: VISTAS Y ACCIONES (orden jerárquico correcto)
        # ========================================== #
        # Primero cashflow (no depende de nadie)
        'views/cashflow_projection_views.xml',
        
        # Después periodic_expense (depende de cashflow)
        'views/periodic_expense_views.xml',
        
        # Después financial_analysis 
        'views/financial_analysis_views.xml',
        'views/account_move_integration_views.xml',
        
        # Al final el dashboard (depende de todos)
        'views/dashboard_main_views.xml',
        
        # ========================================== #
        # PASO 3: PERMISOS (después de que modelos existan)
        # ========================================== #
        'security/ir.model.access.csv',
        
        # ========================================== #
        # PASO 4: DATOS MAESTROS
        # ========================================== #
        'data/expense_category_data.xml',
        'data/cashflow_category_data.xml',
        
        # ========================================== #
        # PASO 5: WIZARDS
        # ========================================== #
        'wizard/cashflow_report_wizard_views.xml',
        'wizard/invoice_import_wizard_views.xml',
        
        # ========================================== #
        # PASO 6: MENÚS
        # ========================================== #
        'views/menu_views.xml',
        
        # ========================================== #
        # PASO 7: REPORTES
        # ========================================== #
        'reports/cashflow_reports.xml',
        'reports/expense_analysis_reports.xml',
        
        # ========================================== #
        # PASO 8: REGLAS AVANZADAS (al final)
        # ========================================== #
        'security/security_rules.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'financial_dashboard/static/src/css/dashboard_style.scss',
            'financial_dashboard/static/src/js/dashboard_widgets.js',
            'financial_dashboard/static/src/js/cashflow_grid.js',
            'financial_dashboard/static/src/xml/dashboard_templates.xml',
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