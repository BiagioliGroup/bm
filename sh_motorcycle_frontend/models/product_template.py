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
        Versión con DEBUG DETALLADO para identificar dónde se aplica el 10% incorrecto
        """
        self.ensure_one()
        
        import logging
        _logger = logging.getLogger(__name__)
        
        # FORZAR DEBUG PARA DROPSHIPPING
        _logger.warning(f"========== INICIO DEBUG get_comparative_prices ==========")
        _logger.warning(f"Producto: {self.name} (ID: {self.id})")
        _logger.warning(f"List Price (Público): ${self.list_price}")
        
        # Validaciones básicas
        if not self.product_variant_ids:
            _logger.warning("No hay variantes de producto")
            return []
            
        user = self.env.user
        if user._is_public():
            _logger.warning("Usuario público - no mostrar precios comparativos")
            return []
            
        website = self.env['website'].get_current_website()
        if not hasattr(website, 'sh_show_comparative_prices') or not website.sh_show_comparative_prices:
            _logger.warning("Website no tiene habilitado mostrar precios comparativos")
            return []
        
        partner = user.partner_id.sudo()
        user_pricelist = partner.property_product_pricelist
        if not user_pricelist:
            _logger.warning("Usuario sin lista de precios")
            return []
        
        _logger.warning(f"Usuario: {user.name} - Lista de precios: {user_pricelist.name}")
        
        product_variant = self.product_variant_ids[0]
        results = []
        prices_found = {}
        
        # Precio público = list_price del producto
        public_price = self.list_price
        
        def calculate_price_manually(pricelist, product_template, product_variant):
            """
            Cálculo manual con DEBUG DETALLADO
            """
            _logger.warning(f"  >>> CALCULANDO precio para lista: '{pricelist.name}'")
            
            try:
                # Buscar reglas aplicables
                all_rules = pricelist.item_ids
                _logger.warning(f"      Total de reglas en la lista: {len(all_rules)}")
                
                for idx, rule in enumerate(all_rules):
                    _logger.warning(f"      Regla {idx+1}:")
                    _logger.warning(f"        - applied_on: {rule.applied_on}")
                    _logger.warning(f"        - compute_price: {rule.compute_price}")
                    _logger.warning(f"        - base: {rule.base}")
                    if rule.base == 'pricelist' and rule.base_pricelist_id:
                        _logger.warning(f"        - base_pricelist: {rule.base_pricelist_id.name}")
                    if rule.compute_price == 'percentage':
                        _logger.warning(f"        - percent_price: {rule.percent_price}%")
                    elif rule.compute_price == 'fixed':
                        _logger.warning(f"        - fixed_price: {rule.fixed_price}")
                    elif rule.compute_price == 'formula':
                        _logger.warning(f"        - discount: {rule.price_discount}%")
                        _logger.warning(f"        - surcharge: {rule.price_surcharge}")
                
                applicable_rules = pricelist.item_ids.filtered(
                    lambda r: (
                        r.applied_on == '3_global' or
                        (r.applied_on == '2_product_category' and r.categ_id in product_template.categ_id._get_parents_and_self()) or
                        (r.applied_on == '1_product' and r.product_tmpl_id == product_template) or
                        (r.applied_on == '0_product_variant' and r.product_id == product_variant)
                    )
                ).sorted(key=lambda r: (r.applied_on, r.min_quantity))
                
                _logger.warning(f"      Reglas aplicables al producto: {len(applicable_rules)}")
                
                if not applicable_rules:
                    _logger.warning(f"      NO HAY REGLAS APLICABLES - Retornando list_price: ${product_template.list_price}")
                    return product_template.list_price
                    
                rule = applicable_rules[0]
                _logger.warning(f"      Usando primera regla aplicable:")
                _logger.warning(f"        - applied_on: {rule.applied_on}")
                _logger.warning(f"        - base: {rule.base}")
                _logger.warning(f"        - compute_price: {rule.compute_price}")
                
                # Obtener precio base
                base_price = None
                
                if rule.base == 'list_price':
                    base_price = product_template.list_price
                    _logger.warning(f"      Base = list_price: ${base_price}")
                    
                elif rule.base == 'standard_price':
                    base_price = product_template.standard_price
                    _logger.warning(f"      Base = standard_price: ${base_price}")
                    
                elif rule.base == 'pricelist':
                    _logger.warning(f"      Base = pricelist")
                    if rule.base_pricelist_id:
                        _logger.warning(f"      Calculando precio desde lista base: {rule.base_pricelist_id.name}")
                        base_price = calculate_price_manually(
                            rule.base_pricelist_id, product_template, product_variant
                        )
                        _logger.warning(f"      Precio obtenido de lista base: ${base_price}")
                        
                        # PUNTO CRÍTICO: Verificar si es dropshipping sin mayorista real
                        if 'dropshipping' in pricelist.name.lower():
                            _logger.warning(f"      *** ES DROPSHIPPING - Verificando si hay precio mayorista real ***")
                            if base_price is None:
                                _logger.warning(f"      *** NO HAY precio en lista mayorista - RETORNANDO None ***")
                                return None
                            elif abs(base_price - product_template.list_price) < 0.01:
                                _logger.warning(f"      *** Precio mayorista ({base_price}) = Precio público ({product_template.list_price}) ***")
                                _logger.warning(f"      *** NO HAY descuento mayorista - RETORNANDO None ***")
                                return None
                            else:
                                _logger.warning(f"      *** SÍ hay precio mayorista diferente - Continuando cálculo ***")
                    else:
                        _logger.warning(f"      NO hay base_pricelist_id configurada")
                        if 'dropshipping' in pricelist.name.lower():
                            _logger.warning(f"      *** Dropshipping sin lista base - RETORNANDO None ***")
                            return None
                        base_price = product_template.list_price
                
                if base_price is None or base_price <= 0:
                    _logger.warning(f"      Base price inválido: {base_price} - RETORNANDO None")
                    return None
                
                # Aplicar cálculo
                final_price = base_price
                
                if rule.compute_price == 'fixed':
                    final_price = rule.fixed_price or 0
                    _logger.warning(f"      Precio fijo: ${final_price}")
                    
                elif rule.compute_price == 'percentage':
                    percent = rule.percent_price or 100.0
                    _logger.warning(f"      Aplicando porcentaje: {percent}%")
                    
                    # DEBUGGING: Ver qué pasa con cada tipo de lista
                    if 'dropshipping' in pricelist.name.lower():
                        _logger.warning(f"      *** DROPSHIPPING detectado ***")
                        _logger.warning(f"      *** Percent value: {percent} ***")
                        _logger.warning(f"      *** Base price: ${base_price} ***")
                        
                        if percent == -10.0:
                            _logger.warning(f"      *** Aplicando margen 10% (percent = -10) ***")
                            final_price = base_price * 1.10
                        else:
                            _logger.warning(f"      *** Aplicando porcentaje estándar ***")
                            final_price = base_price * (percent / 100.0)
                        
                        _logger.warning(f"      *** Final price para dropshipping: ${final_price} ***")
                        
                    elif 'revendedor' in pricelist.name.lower() and percent == 10.0:
                        _logger.warning(f"      REVENDEDOR con 10% descuento")
                        final_price = base_price * 0.90
                    else:
                        final_price = base_price * (percent / 100.0)
                        
                    _logger.warning(f"      Precio después de porcentaje: ${final_price}")
                        
                elif rule.compute_price == 'formula':
                    discount = rule.price_discount or 0.0
                    surcharge = rule.price_surcharge or 0.0
                    _logger.warning(f"      Aplicando fórmula - Descuento: {discount}%, Recargo: {surcharge}")
                    
                    final_price = base_price * (1.0 - discount / 100.0)
                    final_price += surcharge
                    _logger.warning(f"      Precio después de fórmula: ${final_price}")
                
                # Redondeo
                price_round = rule.price_round or 0.01
                if price_round > 0:
                    final_price = round(final_price / price_round) * price_round
                    _logger.warning(f"      Precio después de redondeo: ${final_price}")
                
                _logger.warning(f"  <<< RESULTADO para '{pricelist.name}': ${final_price}")
                return max(final_price, 0.0) if final_price else None
                
            except Exception as e:
                _logger.error(f"ERROR en cálculo para {pricelist.name}: {str(e)}")
                import traceback
                _logger.error(traceback.format_exc())
                return None
        
        # LÓGICA PRINCIPAL
        user_pricelist_name = user_pricelist.name.lower()
        _logger.warning(f"Tipo de usuario detectado: {user_pricelist_name}")
        
        pricelists_to_show = []
        show_public_price = False
        
        if 'dropshipping' in user_pricelist_name:
            _logger.warning("=== PROCESANDO USUARIO DROPSHIPPING ===")
            
            # Buscar lista mayorista
            mayorista_pl = None
            if hasattr(website, 'sh_mayorista_pricelist_ids'):
                for pl in website.sh_mayorista_pricelist_ids:
                    if 'mayorista' in pl.name.lower():
                        mayorista_pl = pl
                        _logger.warning(f"Lista mayorista encontrada en website: {pl.name}")
                        break
            
            if not mayorista_pl:
                mayorista_pl = self.env['product.pricelist'].search([
                    ('name', 'ilike', 'mayorista'),
                    ('company_id', '=', self.env.company.id)
                ], limit=1)
                if mayorista_pl:
                    _logger.warning(f"Lista mayorista encontrada por búsqueda: {mayorista_pl.name}")
                else:
                    _logger.warning("NO se encontró lista mayorista")
            
            if mayorista_pl:
                _logger.warning("Calculando precio mayorista...")
                mayorista_price = calculate_price_manually(mayorista_pl, self, product_variant)
                _logger.warning(f"Precio mayorista calculado: ${mayorista_price}")
                _logger.warning(f"Precio público (list_price): ${public_price}")
                
                # Verificar si hay precio mayorista real
                has_wholesale_price = (
                    mayorista_price is not None and 
                    mayorista_price > 0 and 
                    abs(mayorista_price - public_price) > 0.01
                )
                
                _logger.warning(f"¿Tiene precio mayorista real?: {has_wholesale_price}")
                
                if has_wholesale_price:
                    _logger.warning("SÍ tiene precio mayorista - Calculando precio dropshipping...")
                    dropship_price = calculate_price_manually(user_pricelist, self, product_variant)
                    _logger.warning(f"Precio dropshipping calculado: ${dropship_price}")
                    
                    if dropship_price and dropship_price > 0:
                        pricelists_to_show.append(user_pricelist)
                        show_public_price = True
                        _logger.warning("Mostrando precio dropshipping con etiqueta")
                    else:
                        _logger.warning("No se pudo calcular precio dropshipping - Mostrando solo público")
                        return [{
                            'name': 'Precio',
                            'price': public_price,
                            'is_user_pricelist': True,
                            'pricelist_id': user_pricelist.id,
                        }]
                else:
                    _logger.warning("NO tiene precio mayorista - Debería mostrar solo precio público SIN CAMBIOS")
                    _logger.warning(f"RETORNANDO precio público: ${public_price}")
                    return [{
                        'name': 'Precio',
                        'price': public_price,
                        'is_user_pricelist': True,
                        'pricelist_id': user_pricelist.id,
                    }]
            else:
                _logger.warning("No existe lista mayorista - Mostrando precio público")
                return [{
                    'name': 'Precio',
                    'price': public_price,
                    'is_user_pricelist': True,
                    'pricelist_id': user_pricelist.id,
                }]
        
        elif 'mayorista' in user_pricelist_name:
            _logger.warning("Usuario MAYORISTA")
            pricelists_to_show.append(user_pricelist)
            show_public_price = True
            
        elif 'revendedor' in user_pricelist_name:
            _logger.warning("Usuario REVENDEDOR")
            pricelists_to_show.append(user_pricelist)
            show_public_price = True
            
        else:
            _logger.warning(f"Usuario OTRO: {user_pricelist_name}")
            pricelists_to_show.append(user_pricelist)
            if hasattr(website, 'sh_mayorista_pricelist_ids'):
                for pricelist in website.sh_mayorista_pricelist_ids:
                    if pricelist.id != user_pricelist.id and pricelist.active:
                        pricelists_to_show.append(pricelist)
            show_public_price = True
        
        # Calcular precios
        _logger.warning(f"Calculando precios para {len(pricelists_to_show)} listas...")
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
                _logger.warning(f"Agregado: {pricelist.name} = ${price}")
        
        # Agregar precio público
        if show_public_price and public_price > 0:
            user_price = prices_found.get(user_pricelist.id, 0)
            if not user_price or abs(public_price - user_price) > 0.01:
                results.append({
                    'name': 'Público',
                    'price': public_price,
                    'is_user_pricelist': False,
                    'pricelist_id': -1,
                })
                _logger.warning(f"Agregado precio público: ${public_price}")
        
        # Ordenar resultados
        results.sort(key=lambda x: (not x['is_user_pricelist'], x['price']))
        
        _logger.warning("=== RESULTADOS FINALES ===")
        for r in results:
            _logger.warning(f"  {r['name']}: ${r['price']:.2f} {'[USUARIO]' if r['is_user_pricelist'] else ''}")
        _logger.warning(f"========== FIN DEBUG ==========")
        
        return results