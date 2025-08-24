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
        MÉTODO ADAPTADO - Trabaja con las reglas existentes sin cambiar BD
        """
        self.ensure_one()
        
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
        
        def calculate_price_with_existing_rules(pricelist, product_template, product_variant):
            """
            Calcula precios respetando las reglas EXISTENTES de la BD
            """
            try:
                applicable_rules = pricelist.item_ids.filtered(
                    lambda r: r.applied_on == '3_global'
                ).sorted(key=lambda r: r.sequence)
                
                if not applicable_rules:
                    return None
                    
                rule = applicable_rules[0]
                
                import logging
                _logger = logging.getLogger(__name__)
                _logger.info(f"Regla {pricelist.name}: base={rule.base}, compute={rule.compute_price}, percent={rule.percent_price}")
                
                base_price = None
                
                # Determinar precio base
                if rule.base == 'list_price':
                    base_price = product_template.list_price
                elif rule.base == 'pricelist':
                    if rule.base_pricelist_id:
                        # Para dropshipping basado en mayorista
                        base_price = calculate_price_with_existing_rules(
                            rule.base_pricelist_id, product_template, product_variant
                        )
                        if base_price is None:
                            base_price = product_template.list_price
                    else:
                        base_price = product_template.list_price
                
                if base_price is None or base_price <= 0:
                    return None
                
                final_price = base_price
                
                # LÓGICA ADAPTADA A REGLAS EXISTENTES
                if rule.compute_price == 'percentage':
                    percent = rule.percent_price or 100.0
                    
                    # CASO ESPECIAL: Interpretación según la lista
                    if 'revendedor' in pricelist.name.lower():
                        # Revendedor: "10% descuento" significa aplicar 90%
                        if percent == 10.0:  # Es un descuento del 10%
                            final_price = base_price * 0.90  # 90% del precio original
                            _logger.info(f"  Revendedor: ${base_price} * 90% = ${final_price}")
                        else:
                            final_price = base_price * (percent / 100.0)
                            
                    elif 'dropshipping' in pricelist.name.lower():
                        # Dropshipping: "-10% descuento" = descuento negativo = incremento
                        if percent == -10.0:  # Es -10% (descuento negativo = +10% incremento)
                            final_price = base_price * 1.10  # 110% de la base (mayorista)
                            _logger.info(f"  Dropshipping: ${base_price} * 110% = ${final_price}")
                        else:
                            # Para otros porcentajes negativos, convertir a positivos
                            final_price = base_price * (1 + abs(percent) / 100.0)
                    else:
                        # Otras listas: lógica normal
                        final_price = base_price * (percent / 100.0)
                        
                elif rule.compute_price == 'fixed':
                    final_price = rule.fixed_price or 0
                    
                # Redondeo
                price_round = rule.price_round or 0.01
                if price_round > 0:
                    final_price = round(final_price / price_round) * price_round
                
                return max(final_price, 0.0)
                
            except Exception as e:
                import logging
                _logger = logging.getLogger(__name__)
                _logger.error(f"Error calculando {pricelist.name}: {e}")
                return None
        
        # Lógica de listas a mostrar
        user_pricelist_name = user_pricelist.name.lower()
        pricelists_to_show = [user_pricelist]
        
        # Agregar listas adicionales según el usuario
        if 'dropshipping' in user_pricelist_name:
            # Dropshipping ve: su precio + mayorista + público
            mayorista_pl = self.env['product.pricelist'].search([('name', 'ilike', 'mayorista')], limit=1)
            if mayorista_pl:
                pricelists_to_show.append(mayorista_pl)
        
        # Calcular precios
        for pricelist in pricelists_to_show:
            price = calculate_price_with_existing_rules(pricelist, self, product_variant)
            
            if price and price > 0:
                prices_found[pricelist.id] = price
                results.append({
                    'name': pricelist.name,
                    'price': price,
                    'is_user_pricelist': pricelist.id == user_pricelist.id,
                    'pricelist_id': pricelist.id,
                })
        
        # Agregar precio público si es diferente
        if public_price > 0:
            user_price = prices_found.get(user_pricelist.id, 0)
            if user_price and abs(public_price - user_price) > (public_price * 0.01):
                results.append({
                    'name': 'Público',
                    'price': public_price,
                    'is_user_pricelist': False,
                    'pricelist_id': -1,
                })
        
        # Solo mostrar si hay diferencias
        if len(results) < 2:
            return []
        
        # Log para debugging
        import logging
        _logger = logging.getLogger(__name__)
        _logger.info(f"Usuario {user_pricelist.name}: {len(results)} precios comparativos")
        for r in results:
            _logger.info(f"  - {r['name']}: ${r['price']:.2f}")
        
        results.sort(key=lambda x: (not x['is_user_pricelist'], x['price']))
        return results
