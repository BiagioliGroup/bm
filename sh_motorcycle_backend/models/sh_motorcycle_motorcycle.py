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
