# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models
import logging
_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model
    def _get_type_list(self):
        """
            METHOD BY SOFTHEALER
            to get product type list
        """
        type_list = self.env['motorcycle.type'].sudo().search_read(
            domain=[],
            fields=['id', 'name'],
            order="id asc",
        )
        return type_list or []

    @api.model
    def _get_make_list(self, type_id=None):
        """
            METHOD BY SOFTHEALER
            to get product make list
        """
        make_list = []
        if type_id not in ('', "", None, False):
            if type_id != int:
                type_id = int(type_id)
            search_make_list = self.env['motorcycle.mmodel'].sudo().search_read(
                domain=[('type_id', '=', type_id)],
                fields=['make_id'],
                order="name asc",
            )
            make_dic = {}
            if search_make_list:
                for item_dic in search_make_list:
                    make_tuple = item_dic.get('make_id', False)
                    if make_tuple:
                        make_dic.update(
                            {make_tuple[0]: {'id': make_tuple[0], 'name': make_tuple[1]}})

            if make_dic:
                for key, value in sorted(make_dic.items(), key=lambda kv: kv[1]['name']):
                    make_list.append(value)
        return make_list or []

    @api.model
    def _get_model_list(self, type_id=None, make_id=None):
        """
            METHOD BY SOFTHEALER
            to get product model list
        """
        model_list = []
        if (
            type_id not in ('', "", None, False) and
            make_id not in ('', "", None, False)
        ):
            if type_id != int:
                type_id = int(type_id)
            if make_id != int:
                make_id = int(make_id)
            model_list = self.env['motorcycle.mmodel'].sudo().search_read(
                domain=[
                    ('make_id', '=', make_id),
                    ('type_id', '=', type_id),
                ],
                fields=['id', 'name'],
                order="name asc",
            )
        return model_list or []

    @api.model
    def _get_year_list(self, type_id=None, make_id=None, model_id=None):
        year_list = []
        if type_id and make_id and model_id:
            type_id, make_id, model_id = int(type_id), int(make_id), int(model_id)
            vehicles = self.env['motorcycle.motorcycle'].sudo().search([
                ('type_id', '=', type_id),
                ('make_id', '=', make_id),
                ('mmodel_id', '=', model_id),
            ])
            year_list = sorted(set(vehicle.year for vehicle in vehicles), reverse=True)
        return year_list or []


    # ARCHIVO: sh_motorcycle_frontend/models/product_template.py
    # MÉTODO get_comparative_prices() VERSIÓN FINAL CORREGIDA

    def get_comparative_prices(self):
        """
        Obtiene precios comparativos para mostrar en tienda
        VERSIÓN CORREGIDA: Usa list_price como precio público
        """
        self.ensure_one()
        
        current_user = self.env.user
        
        try:
            website = self.env['website'].get_current_website()
        except:
            website = self.env['website'].search([('company_id', '=', current_user.company_id.id)], limit=1)
        
        # Si no está configurado, no mostrar precios comparativos
        if not hasattr(website, 'sh_show_comparative_prices') or not website.sh_show_comparative_prices:
            return []
        
        # Para usuarios públicos, no mostrar nada
        if current_user._is_public():
            return []
        
        # Obtener el producto variant principal
        product_variant = self.product_variant_ids[0] if self.product_variant_ids else None
        if not product_variant:
            return []
        
        # OBTENER PRICELIST DEL USUARIO
        try:
            is_portal_user = any(
                'portal' in group.name.lower() or group.name == 'Portal' 
                for group in current_user.groups_id
            )
            
            if is_portal_user:
                user_partner = current_user.partner_id.sudo()
                user_pricelist = user_partner.property_product_pricelist
            else:
                user_partner = current_user.partner_id
                user_pricelist = user_partner.property_product_pricelist
                
        except Exception:
            return []
        
        if not user_pricelist:
            return []
        
        # PRECIO PÚBLICO = list_price del producto (NO de una lista)
        public_price = self.list_price
        
        # PRECIO DEL USUARIO = calculado con su pricelist
        try:
            user_price = user_pricelist.sudo()._get_product_price(
                product_variant, 1.0, user_partner, date=False, uom_id=product_variant.uom_id.id
            )
        except Exception:
            return []
        
        # Verificar que los precios sean diferentes
        if abs(user_price - public_price) <= (public_price * 0.001):  # Tolerancia del 0.1%
            return []  # Precios iguales, no mostrar comparativos
        
        # CREAR RESULTADOS
        results = [
            {
                'pricelist_id': 0,  # ID especial para precio público
                'name': 'Público',
                'price': public_price,
                'is_user_pricelist': False,
                'formatted_price': '{:,.2f}'.format(public_price),
            },
            {
                'pricelist_id': user_pricelist.id,
                'name': user_pricelist.name,
                'price': user_price,
                'is_user_pricelist': True,
                'formatted_price': '{:,.2f}'.format(user_price),
            }
        ]
        
        # Ordenar: Usuario primero si es menor, público primero si es menor
        results.sort(key=lambda x: (not x['is_user_pricelist'], x['price']))
        
        return results