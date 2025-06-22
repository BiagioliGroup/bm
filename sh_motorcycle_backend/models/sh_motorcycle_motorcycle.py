# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class Motorcycle(models.Model):
    _name = "motorcycle.motorcycle"
    _description = "Motorcycle"
    _order = "id desc"

    name = fields.Char(compute="_compute_complete_name", store=True)
    type_id = fields.Many2one(comodel_name="motorcycle.type",
                          string="Type",
                          related="mmodel_id.type_id",
                          store=True
                          )
    make_id = fields.Many2one(comodel_name="motorcycle.make",
                              string="Make",
                              related="mmodel_id.make_id",
                              store=True
                              )
    mmodel_id = fields.Many2one("motorcycle.mmodel", string="Model", required=True)
    year = fields.Integer(string="Year", required=True, index=True)
    market = fields.Selection([
        ('EUR', 'Europe'),
        ('USA', 'USA'),
        ('ARG', 'Argentina'),
        ('AUS', 'Australia'),
        ('USA-CAN', 'USA & Canada'),
        ('EURO5+', 'Euro 5+'),
        ('CANADA', 'Canada'),
        ('JP', 'Japan'),
        ('CH', 'China'),
    ], string="Market", required=True, default="USA")

    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.user.company_id.id)
    
    product_ids = fields.Many2many('product.product',
                                   'product_product_motorcycle_motorcycle_rel',
                                   'motorcycle_id', 'product_id',
                                   string='Productos Compatibles', copy=True)
    
    oem_manual = fields.Binary(string="OEM Manual", attachment=True)
    user_manual = fields.Binary(string="User Manual", attachment=True)
    motorcycle_image = fields.Binary(string="Motorcycle Image", attachment=True)

    service_ids = fields.Many2many(
        'motorcycle.service',
        'motorcycle_service_rel',  # nombre de la tabla relacional
        'motorcycle_id',           # campo local en la tabla relacional
        'service_id',              # campo remoto
        string='Servicios asignados',
        compute='_compute_service_ids',
        store=False
    )

    # Agregado 21-06-2025 - para poder agregar datos técnicos a la moto
    # Se relaciona con motorcycle.technical.data
    # Se relaciona con product.category y product.attribute
    # Se relaciona con product.attribute.value para poder agregar el valor del dato técnico
    technical_data_ids = fields.One2many(
            'motorcycle.technical.data',
            'motorcycle_id',
            string='Technical Data'
        )
    # Agregado 21-06-2025 - Fin

    def _compute_service_ids(self):
        for moto in self:
            moto.service_ids = self.env['motorcycle.service'].search([
                ('motorcycle_ids', 'in', moto.id)
            ])
    

    @api.depends("type_id", "make_id", "mmodel_id", "year")
    def _compute_complete_name(self):
        for record in self:
            market = record.market if record.market else ""
            record.name = f"{record.make_id.name} {record.mmodel_id.name} {str(record.year)} {market}"
            #asdsa
            # name_parts = [record.type_id.name, record.make_id.name, record.mmodel_id.name, str(record.year)]
            # record.name = " - ".join(filter(None, name_parts))
    
    
    @api.constrains("year")
    def _check_year(self):
        current_year = fields.Date.today().year
        for record in self:
            if record.year < 1900 or record.year > current_year:
                raise ValidationError(_("The year must be between 1900 and %s.") % current_year)
            
    
    def action_create_service(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Nuevo Servicio',
            'res_model': 'motorcycle.service',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_motorcycle_ids': [self.id],
            },
        }




class MotorcycleTechnicalData(models.Model):
    _name = 'motorcycle.technical.data'
    _description = 'Technical Data for Motorcycles'
    _order = 'motorcycle_id, category_id, attribute_id'

    motorcycle_id = fields.Many2one(
        'motorcycle.motorcycle', string='Motorcycle', required=True, ondelete='cascade'
    )
    category_id = fields.Many2one(
        'product.category', string='Product Category', required=True
    )
    attribute_id = fields.Many2one(
        'product.attribute', string='Attribute', required=True
    )
    value_id = fields.Many2one(
        'product.attribute.value', string='Attribute Value', required=True
    )

    note = fields.Char(string='Extra Note')

    _sql_constraints = [
        ('uniq_entry',
         'unique(motorcycle_id, category_id, attribute_id)',
         'This attribute is already set for this motorcycle and category.'),
    ]

    @api.constrains('attribute_id', 'value_id')
    def _check_value_belongs_to_attribute(self):
        for record in self:
            if record.value_id.attribute_id != record.attribute_id:
                raise ValidationError("The selected value does not match the selected attribute.")
