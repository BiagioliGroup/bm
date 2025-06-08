# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api

class MotorcycleGarage(models.Model):
    _name = "motorcycle.garage"
    _description = "Motorcycle Garage"
    _order = "id desc"
    

    name = fields.Char(compute="_compute_complete_name", store=True)
    user_id = fields.Many2one("res.users", string="User", required=True)
    type_id = fields.Many2one("motorcycle.type", string="Type", required=True)
    make_id = fields.Many2one("motorcycle.make", string="Make", required=True)
    mmodel_id = fields.Many2one("motorcycle.mmodel", string="Model", required=True)
    year = fields.Integer(string="Year", required=True, index=True)

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.user.company_id.id)

    @api.depends("type_id", "make_id", "mmodel_id", "year")
    def _compute_complete_name(self):
        for record in self:
            name_parts = [record.type_id.name, record.make_id.name, record.mmodel_id.name, str(record.year)]
            record.name = " - ".join(filter(None, name_parts))