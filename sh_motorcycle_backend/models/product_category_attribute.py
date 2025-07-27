# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ProductCategory(models.Model):
    _inherit = 'product.category'

    show_in_website = fields.Boolean(
        string='Mostrar en Web',
        default=True,
        help="Si está marcado, aparecerá esta categoría en el sitio web."
    )
    depth = fields.Integer(
        string='Profundidad',
        compute='_compute_depth',
        store=True,
        readonly=True
    )
    attribute_ids = fields.Many2many(
        'product.attribute',
        'product_attribute_category_rel',
        'category_id',
        'attribute_id',
        string='Atributos Técnicos'
    )

    @api.depends('parent_id')
    def _compute_depth(self):
        for cat in self:
            level = 0
            parent = cat.parent_id
            # Sube la cadena de padres hasta llegar a la raíz
            while parent:
                level += 1
                parent = parent.parent_id
            cat.depth = level


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    unit_id = fields.Many2one(
        'product.attribute.unit',
        string='Unidad de Medida',
        help='Unidad en la que se miden los valores de este atributo.'
    )

    @api.model
    def name_get(self):
        """Mostrar la unidad entre paréntesis si está definida."""
        res = []
        for attr in self:
            name = attr.name or ''
            if attr.unit_id:
                name = f"{name} ({attr.unit_id.code})"
            res.append((attr.id, name))
        return res



class ProductAttributeUnit(models.Model):
    _name = 'product.attribute.unit'
    _description = 'Unidad de Medida para Atributos'
    _order = 'name'

    name = fields.Char(string='Nombre de Unidad', required=True)
    code = fields.Char(string='Código (p.ej. mm, cm, in)', required=True)
