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
    # Relación inversa para poder hacer domain desde attribute
    categ_ids = fields.Many2many(
        'product.category',
        'product_attribute_category_rel',
        'attribute_id',
        'category_id',
        string='Categorías Técnicas'
    )

    unit_id = fields.Many2one(
        'uom.uom',
        string='Unidad de Medida',
        help="Unidad en la que se miden los valores de este atributo.",
        # opcional: filtra solo la categoría de unidades que quieras, 
        # p.ej. LENGTH, WEIGHT, etc., según tu configuración de UoM
        domain="[('category_id','=', 'Unit')]"
    )

    @api.model
    def name_get(self):
        """Añade la unidad entre paréntesis tras el nombre si está definida."""
        res = super().name_get()
        # res es [(id, name), ...]
        out = []
        for rec_id, name in res:
            rec = self.browse(rec_id)
            if rec.unit_id:
                # rec.unit_id.name suele ser "Milímetros (mm)" o similar
                name = f"{name} ({rec.unit_id.name})"
            out.append((rec_id, name))
        return out


class ProductAttributeUnit(models.Model):
    _name = 'product.attribute.unit'
    _description = 'Unidad de Medida para Atributos'
    _order = 'name'

    name = fields.Char(string='Nombre de Unidad', required=True)
    code = fields.Char(string='Código (p.ej. mm, cm, in)', required=True)
