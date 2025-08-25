# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import fields, models


class Website(models.Model):
    _inherit = 'website'
    
    # NUEVOS CAMPOS MAYORISTA
    sh_show_user_pricelist_badge = fields.Boolean(
        string="Mostrar lista de precios en header",
        default=True,  # ← CAMBIADO: True por defecto
        help="Muestra el nombre de la lista de precios del usuario en el header"
    )
    sh_show_comparative_prices = fields.Boolean(
        string="Mostrar precios comparativos",
        default=True,  # ← CAMBIADO: True por defecto
        help="Muestra precios de diferentes listas en la tienda"
    )
    sh_mayorista_pricelist_ids = fields.Many2many(
        'product.pricelist',
        'website_sh_mayorista_pricelist_rel',
        'website_id', 'pricelist_id',
        string='Listas de precios visibles',
        help="Listas de precios que se mostrarán como referencia"
    )