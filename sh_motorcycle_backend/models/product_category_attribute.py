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

    @api.depends('attribute_id', 'name', 'attribute_id.unit_id')
    @api.depends_context('show_attribute')
    def _compute_display_name(self):
        # Si no queremos mostrar la etiqueta “Atributo:”,
        # delegamos a la impl original
        if not self.env.context.get('show_attribute', True):
            return super(ProductAttributeValue, self)._compute_display_name()

        for value in self:
            # 1) “Atributo: Valor”
            text = f"{value.attribute_id.name}: {value.name}"
            # 2) Si tiene unidad, la añadimos al final
            if value.attribute_id.unit_id:
                text = f"{text} {value.attribute_id.unit_id.name}"
            value.display_name = text

    @api.model
    def name_get(self):
        """Añade siempre la unidad a la derecha del valor."""
        # Primero traemos la lista original de tu padre, para mantener lógicas de contextos, traducciones, etc.
        original = super(ProductAttributeValue, self).name_get()
        result = []
        for record_id, display in original:
            rec = self.browse(record_id)
            # Determinamos la unidad, si existe
            unit = rec.attribute_id.unit_id
            if unit:
                # Si el name_get base ya tiene ": ", asumo que es "Atributo: Valor"
                # así que sólo añadimos la unidad al final.
                display = f"{display} {unit.name}"
            result.append((record_id, display))
        return result