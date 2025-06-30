# models/res_config_settings.py
from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pricelist_ids_show = fields.Many2many(
        'product.pricelist',
        string='Listas de precios visibles en tienda',
        config_parameter='biagioli_ecom_mayorista.pricelist_ids_show'
    )

    show_user_pricelist_badge = fields.Boolean(
    string="Mostrar lista de precios en el header",
    config_parameter="biagioli_ecom_mayorista.show_user_pricelist_badge"
)
    show_comparative_prices = fields.Boolean(
        string="Mostrar precios comparativos",
        config_parameter="biagioli_ecom_mayorista.show_comparative_prices"
    )

    show_ribbon_by_supplier = fields.Boolean(
        string="Mostrar cintas por proveedor",
        config_parameter="biagioli_ecom_mayorista.show_ribbon_by_supplier"
    )