# -*- coding: utf-8 -*-
from odoo import models, fields

class ProductCategory(models.Model):
    _inherit = 'product.category'
    # Relación N-N con product.attribute, usando la misma tabla relacional
    attribute_ids = fields.Many2many(
        'product.attribute',
        'product_attribute_category_rel',
        'category_id',
        'attribute_id',
        string='Atributos Técnicos'
    )

class ProductAttribute(models.Model):
    _inherit = 'product.attribute'
    # Relación inversa para poder hacer domain desde attribute
    categ_ids = fields.Many2many(
        'product.category',
        'product_attribute_category_rel',
        'attribute_id',
        'category_id',
        string='Categorías Técnicas'
    )
