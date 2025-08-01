# 1. AGREGAR en sh_motorcycle_frontend/models/res_config_settings.py

from odoo import fields, models


class Website(models.Model):
    _inherit = 'website'

    sh_is_show_garage = fields.Boolean("Garage Feature?", default=True)
    sh_do_not_consider_vehicle_over_category = fields.Boolean("Do not consider vehicle when click on category")
    sh_do_not_consider_vehicle_over_attribute = fields.Boolean("Do not consider vehicle when click on attributes")
    sh_do_not_consider_vehicle_over_price = fields.Boolean("Do not consider vehicle when change on min/max price")
    
    # NUEVOS CAMPOS MAYORISTA
    sh_show_user_pricelist_badge = fields.Boolean(
        string="Mostrar lista de precios en header",
        default=False,
        help="Muestra el nombre de la lista de precios del usuario en el header"
    )
    sh_show_comparative_prices = fields.Boolean(
        string="Mostrar precios comparativos",
        default=False,
        help="Muestra precios de diferentes listas en la tienda"
    )
    sh_mayorista_pricelist_ids = fields.Many2many(
        'product.pricelist',
        'website_sh_mayorista_pricelist_rel',
        'website_id', 'pricelist_id',
        string='Listas de precios visibles',
        help="Listas de precios que se mostrarán como referencia"
    )


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    sh_is_show_garage = fields.Boolean(
        related="website_id.sh_is_show_garage",
        string="Garage Feature?",
        readonly=False,
    )
    sh_do_not_consider_vehicle_over_category = fields.Boolean(
        related="website_id.sh_do_not_consider_vehicle_over_category",
        string="Do not consider vehicle when click on category",
        readonly=False,
    )
    sh_do_not_consider_vehicle_over_attribute = fields.Boolean(
        related="website_id.sh_do_not_consider_vehicle_over_attribute",
        string="Do not consider vehicle when click on attributes",
        readonly=False,
    )
    sh_do_not_consider_vehicle_over_price = fields.Boolean(
        related="website_id.sh_do_not_consider_vehicle_over_price",
        string="Do not consider vehicle when change on min/max price",
        readonly=False,
    )
    
    # NUEVOS CAMPOS MAYORISTA
    sh_show_user_pricelist_badge = fields.Boolean(
        related="website_id.sh_show_user_pricelist_badge",
        string="Mostrar lista de precios en header",
        readonly=False,
    )
    sh_show_comparative_prices = fields.Boolean(
        related="website_id.sh_show_comparative_prices",
        string="Mostrar precios comparativos",
        readonly=False,
    )
    sh_mayorista_pricelist_ids = fields.Many2many(
        related="website_id.sh_mayorista_pricelist_ids",
        string="Listas de precios visibles",
        readonly=False,
    )