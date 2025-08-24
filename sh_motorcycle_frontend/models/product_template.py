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
        BASADO EN EL CÓDIGO QUE FUNCIONA - Solo correcciones mínimas
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
        
        # Precio público = list_price del producto
        public_price = self.list_price
        
        def calculate_price_manually(pricelist, product_template, product_variant):
            """Cálculo manual robusto - CON CORRECCIÓN PARA REVENDEDOR"""
            try:
                applicable_rules = pricelist.item_ids.filtered(
                    lambda r: (
                        r.applied_on == '3_global' or
                        (r.applied_on == '2_product_category' and r.categ_id in product_template.categ_id.child_of) or
                        (r.applied_on == '1_product' and r.product_tmpl_id == product_template) or
                        (r.applied_on == '0_product_variant' and r.product_id == product_variant)
                    )
                ).sorted(key=lambda r: (r.applied_on, r.min_quantity))
                
                if not applicable_rules:
                    return None
                    
                rule = applicable_rules[0]
                
                # Obtener precio base
                base_price = None
                
                if rule.base == 'list_price':
                    base_price = product_template.list_price
                elif rule.base == 'standard_price':
                    base_price = product_template.standard_price
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
                
                # Aplicar cálculo
                final_price = base_price
                
                if rule.compute_price == 'fixed':
                    final_price = rule.fixed_price or 0
                elif rule.compute_price == 'percentage':
                    percent = rule.percent_price or 100.0
                    
                    # CORRECCIÓN ESPECÍFICA PARA REVENDEDOR
                    if 'revendedor' in pricelist.name.lower() and percent == 10.0:
                        # Revendedor: 10% en regla significa 10% DESCUENTO = 90% del precio
                        final_price = base_price * 0.90
                    elif 'dropshipping' in pricelist.name.lower() and percent == -10.0:
                        # Dropshipping: DEBE usar precio mayorista como base
                        # Si no hay precio mayorista válido, no calcular dropshipping
                        if rule.base == 'pricelist' and rule.base_pricelist_id:
                            # Ya tenemos base_price del mayorista calculado arriba
                            final_price = base_price * 1.10
                        else:
                            # Sin base mayorista válida, no calcular precio dropshipping
                            return None
                    else:
                        # Lógica normal para otros casos
                        final_price = base_price * (percent / 100.0)
                        
                elif rule.compute_price == 'formula':
                    discount = rule.price_discount or 0.0
                    surcharge = rule.price_surcharge or 0.0
                    min_margin = rule.price_min_margin or 0.0
                    max_margin = rule.price_max_margin or 0.0
                    
                    final_price = base_price * (1.0 - discount / 100.0)
                    final_price += surcharge
                    
                    if min_margin > 0:
                        min_price = base_price * (1.0 + min_margin / 100.0)
                        final_price = max(final_price, min_price)
                        
                    if max_margin > 0:
                        max_price = base_price * (1.0 + max_margin / 100.0)
                        final_price = min(final_price, max_price)
                
                # Aplicar redondeo
                price_round = rule.price_round or 0.01
                if price_round > 0:
                    final_price = round(final_price / price_round) * price_round
                
                return max(final_price, 0.0)
                
            except Exception as e:
                import logging
                _logger = logging.getLogger(__name__)
                _logger.warning(f"Error en cálculo manual para {pricelist.name}: {e}")
                return None
        
        # LÓGICA ESPECÍFICA POR TIPO DE USUARIO
        user_pricelist_name = user_pricelist.name.lower()
        
        # Lista de pricelists a mostrar según el usuario
        pricelists_to_show = []
        
        if 'mayorista' in user_pricelist_name:
            # MAYORISTA: Ve su precio + público
            pricelists_to_show.append(user_pricelist)
            
        elif 'revendedor' in user_pricelist_name:
            # REVENDEDOR: Solo ve su precio + público (NO mayorista)
            pricelists_to_show.append(user_pricelist)
            
        elif 'dropshipping' in user_pricelist_name:
            # DROPSHIPPING: Lógica especial
            
            # Primero verificar si el producto REALMENTE tiene precio mayorista diferente
            mayorista_pl = None
            if hasattr(website, 'sh_mayorista_pricelist_ids'):
                for pl in website.sh_mayorista_pricelist_ids:
                    if 'mayorista' in pl.name.lower():
                        mayorista_pl = pl
                        break
            
            if not mayorista_pl:
                mayorista_pl = self.env['product.pricelist'].search([
                    ('name', 'ilike', 'mayorista')
                ], limit=1)
            
            if mayorista_pl:
                # Verificar si hay precio mayorista real para este producto
                mayorista_price = calculate_price_manually(mayorista_pl, self, product_variant)
                
                if mayorista_price and abs(mayorista_price - public_price) > (public_price * 0.01):
                    # SÍ hay precio mayorista diferente - mostrar dropshipping
                    pricelists_to_show.append(user_pricelist)
                    # NO agregar mayorista - dropshipping no debe verlo
                else:
                    # NO hay precio mayorista real - no mostrar etiquetas dropshipping
                    return []
            else:
                # No existe lista mayorista - no mostrar etiquetas
                return []
                
        else:
            # OTROS USUARIOS: Lógica genérica
            pricelists_to_show.append(user_pricelist)
            if hasattr(website, 'sh_mayorista_pricelist_ids'):
                for pricelist in website.sh_mayorista_pricelist_ids:
                    if pricelist.id != user_pricelist.id and pricelist.active:
                        pricelists_to_show.append(pricelist)
        
        # Calcular precios para listas seleccionadas
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
        
        # AGREGAR PRECIO PÚBLICO solo si es diferente del usuario
        if public_price > 0:
            user_price = prices_found.get(user_pricelist.id, 0)
            
            # CORRECCIÓN: Tolerancia más amplia para dropshipping
            tolerance = 0.02 if 'dropshipping' in user_pricelist_name else 0.001
            
            if user_price and abs(public_price - user_price) > (public_price * tolerance):
                results.append({
                    'name': 'Público',
                    'price': public_price,
                    'is_user_pricelist': False,
                    'pricelist_id': -1,
                })
        
        # VALIDACIÓN FINAL: Solo mostrar si hay diferencias reales
        all_prices = set(prices_found.values())
        if public_price > 0 and len([r for r in results if r['name'] == 'Público']) > 0:
            all_prices.add(public_price)
        
        # Debe haber al menos 2 precios diferentes
        if len(all_prices) <= 1:
            return []
        
        # CORRECCIÓN: Tolerancia más permisiva
        if len(all_prices) >= 2:
            min_price = min(all_prices)
            max_price = max(all_prices)
            
            # Reducir de 0.005 a 0.002 (0.2% en lugar de 0.5%)
            if min_price > 0 and ((max_price - min_price) / min_price) < 0.002:
                return []
        
        # Ordenar: usuario primero, luego por precio
        results.sort(key=lambda x: (not x['is_user_pricelist'], x['price']))
        
        # DEBUG: Log para troubleshooting con más detalle
        import logging
        _logger = logging.getLogger(__name__)
        _logger.info(f"=== DEBUG get_comparative_prices ===")
        _logger.info(f"Usuario: {user_pricelist.name}")
        _logger.info(f"Precios calculados: {len(prices_found)}")
        for pl_id, price in prices_found.items():
            pl_name = self.env['product.pricelist'].browse(pl_id).name
            _logger.info(f"  - {pl_name}: ${price:.2f}")
        _logger.info(f"Resultados finales: {len(results)}")
        for r in results:
            _logger.info(f"  - {r['name']}: ${r['price']:.2f} {'(USUARIO)' if r['is_user_pricelist'] else ''}")
        
        return results