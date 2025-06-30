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

        pricelist_name = None
        if request.website.user_id.id != request.env.user.id:  # Si hay usuario logueado distinto al público
            user_partner = request.env.user.partner_id
            if user_partner and user_partner.property_product_pricelist:
                pricelist_name = user_partner.property_product_pricelist.name

        context.update({
            'show_user_pricelist_badge': show_badge,
            'user_pricelist_name': pricelist_name,
        })
        return context
