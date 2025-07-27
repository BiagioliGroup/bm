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
        help="Unidad en la que se miden los valores de este atributo."
        # opcional: filtra solo la categoría de unidades que quieras, 
        # p.ej. LENGTH, WEIGHT, etc., según tu configuración de UoM
       
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


""" Agregamos este método para que los valores de atributos muestren la unidad si está definida.
   Esto es útil para que los usuarios vean la unidad al seleccionar un valor de atributo."""

class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    @api.depends('attribute_id', 'name')
    @api.depends_context('show_attribute')
    def _compute_display_name(self):
        """Incluimos la unidad al final del valor si existe."""
        # Si no queremos mostrar atributo (context.show_attribute=False), delegamos
        if not self.env.context.get('show_attribute', True):
            return super()._compute_display_name()
        for value in self:
            # Primero formamos "[Atributo]: [Valor]"
            base = f"{value.attribute_id.name}: {value.name}"
            # Luego, si su atributo padre tiene unidad, la añadimos
            uom = value.attribute_id.unit_id
            if uom:
                # uom.name suele ser "Milímetros (mm)" o similar
                base = f"{base} {uom.name}"
            value.display_name = base