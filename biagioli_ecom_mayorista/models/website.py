# models/website.py
from odoo import models
from odoo.http import request

class Website(models.Model):
    _inherit = "website"

    def get_website_context(self):
        context = super().get_website_context()
        show_badge = request.env['ir.config_parameter'].sudo().get_param(
            'biagioli_ecom_mayorista.show_user_pricelist_badge', default='False'
        ) == 'True'
        context.update({
            'show_user_pricelist_badge': show_badge,
        })
        return context
