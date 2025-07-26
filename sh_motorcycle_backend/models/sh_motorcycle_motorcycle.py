# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class MotorcycleTechnicalData(models.Model):
    _name = 'motorcycle.technical.data'
    _description = 'Datos Técnicos de la Motocicleta'
    _order = 'motorcycle_id, category_id, attribute_id'

    motorcycle_id = fields.Many2one(
        'motorcycle.motorcycle', string='Motocicleta', required=True, ondelete='cascade'
    )
    category_id = fields.Many2one(
        'product.category', string='Categoría de Producto', required=True
    )
    attribute_id = fields.Many2one(
        'product.attribute', string='Atributo', required=True
    )
    value_id = fields.Many2one(
        'product.attribute.value', string='Valor de Atributo', required=True
    )

    note = fields.Char(string='Nota Adicional')

    _sql_constraints = [
        ('uniq_entry',
         'unique(motorcycle_id, category_id, attribute_id)',
         'Este atributo ya está definido para esta motocicleta y categoría.'),
    ]

    @api.onchange('category_id')
    def _onchange_category_id(self):
        self.attribute_id = False
        self.value_id = False
        return {
            'domain': {
                # sólo atributos vinculados a la categoría elegida
                'attribute_id': [('id', 'in', self.category_id.attribute_ids.ids)],
                # y no permitir valores huérfanos
                'value_id': [('attribute_id', '=', False)],
            }
        }

    @api.onchange('attribute_id')
    def _onchange_attribute_id(self):
        # Al cambiar atributo, limpiamos valor y limitamos los posibles
        self.value_id = False
        return {
            'domain': {
                'value_id': [('attribute_id', '=', self.attribute_id.id)]
            }
        }

    @api.constrains('attribute_id', 'value_id')
    def _check_value_belongs_to_attribute(self):
        for record in self:
            if record.value_id.attribute_id != record.attribute_id:
                raise ValidationError(
                    _('El valor seleccionado no coincide con el atributo.')
                )


class Motorcycle(models.Model):
    _name = "motorcycle.motorcycle"
    _description = "Motocicleta"
    _order = "id desc"

    name = fields.Char(compute="_compute_complete_name", store=True)
    type_id = fields.Many2one(
        comodel_name="motorcycle.type",
        string="Tipo",
        related="mmodel_id.type_id",
        store=True
    )
    make_id = fields.Many2one(
        comodel_name="motorcycle.make",
        string="Marca",
        related="mmodel_id.make_id",
        store=True
    )
    mmodel_id = fields.Many2one(
        "motorcycle.mmodel", string="Modelo", required=True
    )
    year = fields.Integer(string="Año", required=True, index=True)
    market = fields.Selection([
        ('EUR', 'Europa'),
        ('USA', 'EEUU'),
        ('ARG', 'Argentina'),
        ('AUS', 'Australia'),
        ('USA-CAN', 'EEUU y Canadá'),
        ('EURO5+', 'Euro 5+'),
        ('CANADA', 'Canadá'),
        ('JP', 'Japón'),
        ('CH', 'China'),
    ], string="Mercado", required=True, default="USA")

    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        default=lambda self: self.env.user.company_id.id
    )

    product_ids = fields.Many2many(
        'product.product',
        'product_product_motorcycle_motorcycle_rel',
        'motorcycle_id', 'product_id',
        string='Productos Compatibles', copy=True
    )

    oem_manual = fields.Binary(string="Manual OEM", attachment=True)
    user_manual = fields.Binary(string="Manual de Usuario", attachment=True)
    motorcycle_image = fields.Binary(string="Imagen de Motocicleta", attachment=True)

    service_ids = fields.Many2many(
        'motorcycle.service',
        'motorcycle_service_rel',
        'motorcycle_id',
        'service_id',
        string='Servicios asignados',
        compute='_compute_service_ids',
        store=False
    )

    technical_data_ids = fields.One2many(
        'motorcycle.technical.data',
        'motorcycle_id',
        string='Datos Técnicos'
    )

    def _compute_service_ids(self):
        for moto in self:
            moto.service_ids = self.env['motorcycle.service'].search([
                ('motorcycle_ids', 'in', moto.id)
            ])

    @api.depends("type_id", "make_id", "mmodel_id", "year")
    def _compute_complete_name(self):
        for record in self:
            parts = [
                record.make_id.name or '',
                record.mmodel_id.name or '',
                str(record.year),
                record.market or ''
            ]
            record.name = " ".join(filter(None, parts))

    @api.constrains("year")
    def _check_year(self):
        current_year = fields.Date.today().year
        for record in self:
            if record.year < 1900 or record.year > current_year:
                raise ValidationError(
                    _('El año debe estar entre 1900 y %s.') % current_year
                )

    def action_create_service(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Nuevo Servicio'),
            'res_model': 'motorcycle.service',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_motorcycle_ids': [self.id],
            },
        }
