# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api

class MotorcycleYear(models.Model):
    _name = "motorcycle.year"
    _description = "Motorcycle Year"
    _order = "year desc"

    year = fields.Integer(string="Year", required=True, unique=True, index=True)

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.user.company_id.id)

    @api.constrains("year")
    def _check_year(self):
        current_year = fields.Date.today().year
        for record in self:
            if record.year < 1900 or record.year > current_year:
                raise ValidationError(_("The year must be between 1900 and %s.") % current_year)    
            