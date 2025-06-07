# -*- coding: utf-8 -*-
{
    'name': 'Editor Avanzado de Listas de Precios',
    'summary': 'Mejoras en la gestión y edición masiva de reglas de precios',
    'description': """
Este módulo extiende las funcionalidades estándar de Odoo para la gestión de listas de precios, permitiendo una edición más ágil, masiva y controlada de reglas de precios sobre productos.

🚀 Funcionalidades principales:
-------------------------------------
- Nueva vista tipo lista (tree) editable directamente desde el listado.
- Permite modificar en línea los campos clave de las reglas de precios: producto, fecha de inicio y fin, cantidad mínima, etc.
- Agrega un menú exclusivo bajo el apartado "Listas de precios" para acceder al editor.
- Mejora la experiencia de usuarios que gestionan grandes volúmenes de reglas de precios.
- Prepara el sistema para integraciones futuras como duplicaciones automáticas, historial de precios y ajustes por porcentaje o monto.

Ideal para empresas que manejan múltiples listas de precios y requieren eficiencia en el mantenimiento de tarifas.
""",

    'author': 'Biagioli Group',
    'website': 'https://www.biagioligroup.com.ar',

    'category': 'Ventas',
    'version': '1.0',

    'depends': [
        'product',
        'website_sale',  # Requerido si estás integrando con funcionalidades de eCommerce
    ],

    'data': [
        'security/ir.model.access.csv',
        'views/reglas_de_listas_de_precios.xml',
        'views/mass_edit_pricelist_dates_view.xml',
        'views/mass_edit_pricelist_dates_action.xml',
        'views/product_product_price_readonly.xml',
    ],

    'installable': True,
    'application': False,
    'auto_install': False,

    'license': 'LGPL-3',
}
