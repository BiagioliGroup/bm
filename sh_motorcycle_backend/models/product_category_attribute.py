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

    @api.model
    def name_get(self):
        """Si el atributo tiene unidad, la agregamos al nombre del valor."""
        # llama al name_get original para mantener posibles traducciones u otras lógicas
        res = super(ProductAttributeValue, self).name_get()
        out = []
        for val_id, name in res:
            val = self.browse(val_id)
            unit = False
            if val.attribute_id.unit_id:
                # Si usas uom.uom, val.attribute_id.unit_id.name incluye tanto “Milímetros (mm)”
                # Si quieres sólo el código, podrías usar val.attribute_id.unit_id.uom_type.code, 
                # o almacenar el código en otro campo.
                unit = val.attribute_id.unit_id.name
            if unit:
                name = f"{name} {unit}"
            out.append((val_id, name))
        return out
