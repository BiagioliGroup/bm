# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import fields, models, api
from odoo.osv import expression
import re

class ProductProduct(models.Model):
    _inherit = "product.product"
    
    motorcycle_ids = fields.Many2many(
        'motorcycle.motorcycle',
        'product_product_motorcycle_motorcycle_rel',
        'product_id', 'motorcycle_id',
        string='Auto Parts', copy=True
    )
    sh_is_common_product = fields.Boolean(string = "Common Products?")

    @api.onchange('sh_is_common_product')
    def onchange_sh_is_common_product(self):
        if self:
            for record in self:
                if record.sh_is_common_product:
                    record.motorcycle_ids = False
    
    @api.onchange('motorcycle_ids')
    def onchange_sh_motorcycle_ids(self):
        if self:
            for record in self:
                if record.motorcycle_ids:
                    record.sh_is_common_product = False




# class MotorcycleService(models.Model):
#     _name = 'motorcycle.service'
#     _description = 'Servicio técnico para motocicleta'
#     _order = 'motorcycle_id, id'

#     motorcycle_id = fields.Many2one(
#         'motorcycle.motorcycle',
#         required=True,
#         string="Motocicleta"
#     )

#     service_product_ids = fields.Many2many(
#         'product.product',
#         'motorcycle_service_product_rel',
#         'service_id', 'product_id',
#         domain="[('type', '=', 'service')]",
#         string="Servicios de mano de obra"
#     )

#     step_ids = fields.One2many('motorcycle.service.step', 'service_id', string="Checklist de pasos")

#     description = fields.Text('Descripción general')
#     labor_description = fields.Text('Mano de obra a realizar')

#     service_product_line_ids = fields.One2many(
#         'motorcycle.service.product.line',
#         'service_id',
#         string='Repuestos a utilizar'
#     )

#     currency_id = fields.Many2one(
#         'res.currency',
#         string="Moneda",
#         default=lambda self: self.env.company.currency_id.id
#     )

#     total_labor_cost = fields.Monetary(
#         string="Costo total de mano de obra",
#         compute="_compute_total_labor_cost",
#         store=True
#     )

#     total_parts_cost = fields.Monetary(
#         string="Costo total de repuestos",
#         compute="_compute_total_parts_cost",
#         store=True
#     )

#     total_service_cost = fields.Monetary(
#         string="Costo total del servicio",
#         compute="_compute_total_service_cost",
#         store=True
#     )

#     @api.depends('service_product_ids')
#     def _compute_total_labor_cost(self):
#         for record in self:
#             total = sum(product.list_price for product in record.service_product_ids)
#             record.total_labor_cost = total

#     @api.depends('service_product_line_ids.subtotal')
#     def _compute_total_parts_cost(self):
#         for record in self:
#             record.total_parts_cost = sum(line.subtotal for line in record.service_product_line_ids)

#     @api.depends('total_labor_cost', 'total_parts_cost')
#     def _compute_total_service_cost(self):
#         for record in self:
#             record.total_service_cost = record.total_labor_cost + record.total_parts_cost


# class MotorcycleServiceStep(models.Model):
#     _name = 'motorcycle.service.step'
#     _description = 'Paso operativo del servicio técnico'
#     _order = 'sequence, id'

#     service_id = fields.Many2one(
#         'motorcycle.service',
#         string="Servicio de moto",
#         required=True,
#         ondelete='cascade'
#     )

#     name = fields.Char('Descripción del paso', required=True)
#     is_done = fields.Boolean('Completado')
#     note = fields.Text('Nota o instrucción especial')
#     pdf_file = fields.Binary('Archivo PDF', attachment=True)
#     pdf_filename = fields.Char('Nombre del archivo')
#     sequence = fields.Integer('Secuencia', default=10)


# class MotorcycleServiceProductLine(models.Model):
#     _name = 'motorcycle.service.product.line'
#     _description = 'Línea de productos del servicio'

#     service_id = fields.Many2one(
#         'motorcycle.service',
#         string='Servicio',
#         required=True,
#         ondelete='cascade'
#     )

#     product_id = fields.Many2one(
#         'product.product',
#         string='Producto',
#         required=True,
#         domain="[('type', '=', 'product')]"
#     )

#     quantity = fields.Float(
#         string='Cantidad',
#         default=1.0,
#         required=True
#     )

#     price_unit = fields.Float(
#         string='Precio unitario',
#         related='product_id.list_price',
#         readonly=True
#     )

#     subtotal = fields.Float(
#         string='Subtotal',
#         compute='_compute_subtotal',
#         store=True
#     )

#     @api.depends('quantity', 'price_unit')
#     def _compute_subtotal(self):
#         for line in self:
#             line.subtotal = line.quantity * line.price_unit
