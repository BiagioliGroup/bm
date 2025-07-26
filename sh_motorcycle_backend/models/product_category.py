# -*- coding: utf-8 -*-
from odoo import models, fields

class ProductCategory(models.Model):
    _inherit = 'product.category'

    attribute_ids = fields.Many2many(
        'product.attribute',              # modelo destino
        'product_attribute_category_rel', # tabla relacional
        'category_id',                    # campo local
        'attribute_id',                   # campo remoto
        string='Atributos Técnicos'
    )
