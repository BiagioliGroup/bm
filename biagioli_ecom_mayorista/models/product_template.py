# models/product_template.py
from odoo import models

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def get_comparative_prices(self):
        self.ensure_one()
        user = self.env.user
        partner = user.partner_id
        pricelist_partner = partner.property_product_pricelist
        if not pricelist_partner:
            return [] 

        # Precios configurados en Ajustes
        visible_pricelists_raw = self.env['ir.config_parameter'].sudo().get_param(
            'biagioli_ecom_mayorista.pricelist_ids_show', default='[]'
        )
        visible_ids = list(map(int, visible_pricelists_raw.strip('[]').split(','))) if visible_pricelists_raw else []

        visible_ids.append(pricelist_partner.id) if pricelist_partner.id not in visible_ids else None
        visible_ids = list(set(visible_ids))  # remover duplicados

        pricelists = self.env['product.pricelist'].browse(visible_ids)

        results = []
        for pricelist in pricelists:
            price = pricelist._get_product_price(self, 1.0, partner)
            results.append({
                'name': pricelist.name,
                'price': price,
                'is_user_pricelist': pricelist.id == pricelist_partner.id,
            })

        return results
