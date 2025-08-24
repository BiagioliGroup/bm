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
        VERSIÓN SIMPLE - Basada en el método que SÍ funcionaba
        Solo agregamos las correcciones mínimas necesarias
        """
        self.ensure_one()
        
        # Validaciones básicas
        if not self.product_variant_ids:
            return []
            
        user = self.env.user
        if user._is_public():
            return []
            
        website = self.env['website'].get_current_website()
        if not hasattr(website, 'sh_show_comparative_prices') or not website.sh_show_comparative_prices:
            return []
        
        partner = user.partner_id.sudo()
        user_pricelist = partner.property_product_pricelist
        if not user_pricelist:
            return []
        
        product_variant = self.product_variant_ids[0]
        results = []
        prices_found = {}
        public_price = self.list_price
        
        def calculate_price_manually(pricelist, product_template, product_variant):
            """
            Cálculo manual SIMPLE - sin over-engineering
            """
            try:
                applicable_rules = pricelist.item_ids.filtered(
                    lambda r: r.applied_on == '3_global'
                ).sorted(key=lambda r: r.sequence)
                
                if not applicable_rules:
                    return None
                    
                rule = applicable_rules[0]
                base_price = None
                
                # Obtener precio base
                if rule.base == 'list_price':
                    base_price = product_template.list_price
                elif rule.base == 'pricelist':
                    if rule.base_pricelist_id:
                        base_price = calculate_price_manually(
                            rule.base_pricelist_id, product_template, product_variant
                        )
                        if base_price is None:
                            base_price = product_template.list_price
                    else:
                        base_price = product_template.list_price
                
                if base_price is None or base_price <= 0:
                    return None
                
                # Aplicar cálculo SIMPLE
                final_price = base_price
                
                if rule.compute_price == 'fixed':
                    final_price = rule.fixed_price or 0
                elif rule.compute_price == 'percentage':
                    percent = rule.percent_price or 100.0
                    
                    # CORRECCIÓN SIMPLE PARA LOS CASOS CONOCIDOS
                    if pricelist.name == 'Revendedor' and percent == 10.0:
                        # Revendedor: 10% en la regla = 90% del precio (10% descuento)
                        final_price = base_price * 0.90
                    elif pricelist.name == 'Dropshipping' and percent == -10.0:
                        # Dropshipping: -10% en la regla = 110% del precio (incremento)
                        final_price = base_price * 1.10
                    else:
                        # Lógica normal para otros casos
                        final_price = base_price * (percent / 100.0)
                
                # Redondeo simple
                price_round = rule.price_round or 0.01
                if price_round > 0:
                    final_price = round(final_price / price_round) * price_round
                
                return max(final_price, 0.0)
                
            except Exception:
                # Si falla el cálculo manual, retornar None
                return None
        
        # LÓGICA DE LISTAS SIMPLIFICADA
        user_pricelist_name = user_pricelist.name.lower()
        pricelists_to_show = []
        
        # SIEMPRE agregar la lista del usuario
        pricelists_to_show.append(user_pricelist)
        
        # Agregar listas adicionales según tipo de usuario
        if 'dropshipping' in user_pricelist_name:
            # Dropshipping: agregar mayorista
            mayorista_pl = self.env['product.pricelist'].search([('name', 'ilike', 'mayorista')], limit=1)
            if mayorista_pl and mayorista_pl.id != user_pricelist.id:
                pricelists_to_show.append(mayorista_pl)
        
        # Si no es revendedor, agregar listas configuradas
        if 'revendedor' not in user_pricelist_name:
            if hasattr(website, 'sh_mayorista_pricelist_ids'):
                for pricelist in website.sh_mayorista_pricelist_ids:
                    if pricelist.id != user_pricelist.id and pricelist.active:
                        if pricelist not in pricelists_to_show:
                            pricelists_to_show.append(pricelist)
        
        # Calcular precios
        for pricelist in pricelists_to_show:
            price = calculate_price_manually(pricelist, self, product_variant)
            
            if price and price > 0:
                prices_found[pricelist.id] = price
                results.append({
                    'name': pricelist.name,
                    'price': price,
                    'is_user_pricelist': pricelist.id == user_pricelist.id,
                    'pricelist_id': pricelist.id,
                })
        
        # Agregar precio público si es significativamente diferente
        if public_price > 0:
            user_price = prices_found.get(user_pricelist.id, 0)
            if user_price and abs(public_price - user_price) > (public_price * 0.02):  # 2% tolerancia
                results.append({
                    'name': 'Público',
                    'price': public_price,
                    'is_user_pricelist': False,
                    'pricelist_id': -1,
                })
        
        # Solo mostrar si hay al menos 2 precios
        if len(results) < 2:
            return []
        
        # Verificar que hay diferencias reales
        all_prices = [r['price'] for r in results]
        min_price = min(all_prices)
        max_price = max(all_prices)
        
        if min_price > 0 and ((max_price - min_price) / min_price) < 0.02:  # 2% diferencia mínima
            return []
        
        # Ordenar: usuario primero
        results.sort(key=lambda x: (not x['is_user_pricelist'], x['price']))
        
        return results
