# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import fields, models, api


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


from odoo import models, fields, api

class MotorcycleService(models.Model):
    _name = 'motorcycle.service'
    _description = 'Servicio técnico para motocicleta'
    _order = 'motorcycle_id, id'

    motorcycle_id = fields.Many2one(
        'motorcycle.motorcycle',
        required=True,
        string="Motocicleta"
    )

    service_product_ids = fields.Many2many(
        'product.product',
        'motorcycle_service_product_rel',
        'service_id', 'product_id',
        domain="[('type', '=', 'service')]",
        string="Servicios de mano de obra"
    )

    step_ids = fields.One2many('motorcycle.service.step', 'service_id', string="Checklist de pasos")


    description = fields.Text('Descripción general')
    labor_description = fields.Text('Mano de obra a realizar')

    product_ids = fields.Many2many(
        'product.product',
        'motorcycle_service_parts_rel',
        'service_id', 'product_id',
        string='Repuestos a utilizar',
        domain="[('type', '=', 'product')]"
    )

    total_labor_cost = fields.Monetary(
        string="Costo total de mano de obra",
        compute="_compute_total_labor_cost",
        store=True
    )

    currency_id = fields.Many2one(
        'res.currency',
        string="Moneda",
        default=lambda self: self.env.company.currency_id.id
    )

    @api.depends('service_product_ids')
    def _compute_total_labor_cost(self):
        for record in self:
            total = sum(product.list_price for product in record.service_product_ids)
            record.total_labor_cost = total


class MotorcycleServiceStep(models.Model):
    _name = 'motorcycle.service.step'
    _description = 'Paso operativo del servicio técnico'
    _order = 'sequence, id'

    service_id = fields.Many2one(
        'motorcycle.service',
        string="Servicio de moto",
        required=True,
        ondelete='cascade'
    )

    name = fields.Char('Descripción del paso', required=True)
    is_done = fields.Boolean('Completado')
    note = fields.Text('Nota o instrucción especial')
    pdf_file = fields.Binary('Archivo PDF', attachment=True)
    pdf_filename = fields.Char('Nombre del archivo')
    sequence = fields.Integer('Secuencia', default=10)
