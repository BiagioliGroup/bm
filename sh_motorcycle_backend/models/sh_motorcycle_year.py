# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class MotorcycleYear(models.Model):
    _name = "motorcycle.year"
    _description = "Año de Motocicleta"
    _order = "year desc"

    year = fields.Integer(
        string="Año",
        required=True,
        unique=True,
        index=True
    )

    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        default=lambda self: self.env.user.company_id.id
    )

    @api.constrains("year")
    def _check_year(self):
        current_year = fields.Date.today().year
        for record in self:
            if record.year < 1900 or record.year > current_year:
                raise ValidationError(
                    _('El año debe estar entre 1900 y %s.') % current_year
                )
