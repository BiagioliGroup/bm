# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields


class MotorcycleMmodel(models.Model):
    _name = "motorcycle.mmodel"
    _description = "Modelo de Motocicleta"
    _order = "id desc"

    name = fields.Char(string="Nombre", required=True)
    make_id = fields.Many2one(
        comodel_name="motorcycle.make",
        string="Marca", required=True
    )
    type_id = fields.Many2one(
        comodel_name="motorcycle.type",
        string="Tipo", required=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        default=lambda self: self.env.user.company_id.id
    )
