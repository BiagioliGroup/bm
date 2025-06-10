{
    "name": "ARCA DDJJ Integration",
    "version": "1.0",
    "depends": ["base", "account"],
    "author": "Moto Integrale",
    "category": "Accounting",
    "summary": "Descarga y cruza comprobantes de ARCA con Odoo para armar la DDJJ",
    "data": [
        "views/comprobante_arca_views.xml",
        "views/user_arca_views.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
    "application": False,
}
