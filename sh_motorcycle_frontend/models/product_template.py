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
        Método corregido para manejar precios comparativos.
        IMPORTANTE: "Público" no es una lista de precios, es el list_price del producto.
        """
        self.ensure_one()
        
        # Validaciones básicas siguiendo el patrón de Odoo
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
        
        # Precio público = list_price del producto (NO es una pricelist)
        public_price = self.list_price
        
        def calculate_price_manually(pricelist, product_template, product_variant):
            """
            Cálculo manual del precio según las reglas de la lista de precios.
            Retorna None si no puede calcular o si el precio no es válido.
            """
            try:
                # Buscar reglas aplicables
                applicable_rules = pricelist.item_ids.filtered(
                    lambda r: (
                        r.applied_on == '3_global' or
                        (r.applied_on == '2_product_category' and r.categ_id in product_template.categ_id._get_parents_and_self()) or
                        (r.applied_on == '1_product' and r.product_tmpl_id == product_template) or
                        (r.applied_on == '0_product_variant' and r.product_id == product_variant)
                    )
                ).sorted(key=lambda r: (r.applied_on, r.min_quantity))
                
                if not applicable_rules:
                    # Sin reglas aplicables, retornar el precio público
                    return product_template.list_price
                    
                rule = applicable_rules[0]
                
                # Obtener precio base según configuración
                base_price = None
                
                if rule.base == 'list_price':
                    # Usar el precio público del producto
                    base_price = product_template.list_price
                    
                elif rule.base == 'standard_price':
                    # Usar el precio de costo
                    base_price = product_template.standard_price
                    
                elif rule.base == 'pricelist':
                    # Usar otra lista de precios como base
                    if rule.base_pricelist_id:
                        # Calcular recursivamente con la lista base
                        base_price = calculate_price_manually(
                            rule.base_pricelist_id, product_template, product_variant
                        )
                        
                        # VALIDACIÓN CRÍTICA PARA DROPSHIPPING:
                        # Si la lista base (mayorista) no tiene precio diferente al público,
                        # entonces no hay precio mayorista real
                        if 'dropshipping' in pricelist.name.lower():
                            if base_price is None:
                                # No hay precio en la lista mayorista
                                return None
                            elif abs(base_price - product_template.list_price) < 0.01:
                                # El precio mayorista es igual al público - no hay descuento mayorista
                                return None
                    else:
                        # No hay lista base configurada
                        if 'dropshipping' in pricelist.name.lower():
                            # Dropshipping sin lista base no puede calcular
                            return None
                        base_price = product_template.list_price
                
                # Si no se pudo obtener precio base válido
                if base_price is None or base_price <= 0:
                    return None
                
                # Aplicar el método de cálculo según la regla
                final_price = base_price
                
                if rule.compute_price == 'fixed':
                    # Precio fijo
                    final_price = rule.fixed_price or 0
                    
                elif rule.compute_price == 'percentage':
                    # Porcentaje sobre el precio base
                    percent = rule.percent_price or 100.0
                    
                    # Interpretación específica según el tipo de lista
                    if 'revendedor' in pricelist.name.lower() and percent == 10.0:
                        # Revendedor con 10% significa 10% de descuento
                        final_price = base_price * 0.90
                    elif 'dropshipping' in pricelist.name.lower() and percent == -10.0:
                        # Dropshipping con -10% significa 10% de margen adicional
                        final_price = base_price * 1.10
                    else:
                        # Interpretación estándar de Odoo
                        final_price = base_price * (percent / 100.0)
                        
                elif rule.compute_price == 'formula':
                    # Fórmula compleja
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
                
                # Aplicar redondeo si está configurado
                price_round = rule.price_round or 0.01
                if price_round > 0:
                    final_price = round(final_price / price_round) * price_round
                
                return max(final_price, 0.0) if final_price else None
                
            except Exception as e:
                import logging
                _logger = logging.getLogger(__name__)
                _logger.warning(f"Error calculando precio para lista '{pricelist.name}': {str(e)}")
                return None
        
        # LÓGICA PRINCIPAL: Determinar qué mostrar según el tipo de usuario
        user_pricelist_name = user_pricelist.name.lower()
        
        # Determinar qué listas de precios mostrar
        pricelists_to_show = []
        show_public_price = False
        
        if 'mayorista' in user_pricelist_name:
            # MAYORISTA: Ve su precio especial
            pricelists_to_show.append(user_pricelist)
            show_public_price = True  # Mostrar precio público como referencia
            
        elif 'revendedor' in user_pricelist_name:
            # REVENDEDOR: Ve su precio especial
            pricelists_to_show.append(user_pricelist)
            show_public_price = True  # Mostrar precio público como referencia
            
        elif 'dropshipping' in user_pricelist_name:
            # DROPSHIPPING: Caso especial
            
            # Primero verificar si este producto tiene precio mayorista
            mayorista_pl = None
            
            # Buscar lista mayorista en la configuración del website
            if hasattr(website, 'sh_mayorista_pricelist_ids'):
                for pl in website.sh_mayorista_pricelist_ids:
                    if 'mayorista' in pl.name.lower():
                        mayorista_pl = pl
                        break
            
            # Si no está en el website, buscar en todas las listas
            if not mayorista_pl:
                mayorista_pl = self.env['product.pricelist'].search([
                    ('name', 'ilike', 'mayorista'),
                    ('company_id', '=', self.env.company.id)
                ], limit=1)
            
            if mayorista_pl:
                # Calcular precio mayorista para este producto
                mayorista_price = calculate_price_manually(mayorista_pl, self, product_variant)
                
                # Verificar si hay precio mayorista real (diferente al público)
                has_wholesale_price = (
                    mayorista_price is not None and 
                    mayorista_price > 0 and 
                    abs(mayorista_price - public_price) > (public_price * 0.01)  # Más de 1% diferencia
                )
                
                if has_wholesale_price:
                    # Sí hay precio mayorista - calcular y mostrar precio dropshipping
                    dropship_price = calculate_price_manually(user_pricelist, self, product_variant)
                    
                    if dropship_price and dropship_price > 0:
                        # Mostrar precio dropshipping calculado
                        pricelists_to_show.append(user_pricelist)
                        show_public_price = True  # Mostrar precio público como referencia
                    else:
                        # No se pudo calcular precio dropshipping
                        # Mostrar solo precio público sin etiquetas
                        return [{
                            'name': 'Precio',
                            'price': public_price,
                            'is_user_pricelist': True,
                            'pricelist_id': user_pricelist.id,
                        }]
                else:
                    # NO hay precio mayorista diferente al público
                    # Para dropshipping, mostrar el precio público sin etiquetas especiales
                    return [{
                        'name': 'Precio',
                        'price': public_price,
                        'is_user_pricelist': True,
                        'pricelist_id': user_pricelist.id,
                    }]
            else:
                # No existe lista mayorista configurada
                # Mostrar precio público sin etiquetas
                return [{
                    'name': 'Precio',
                    'price': public_price,
                    'is_user_pricelist': True,
                    'pricelist_id': user_pricelist.id,
                }]
                
        else:
            # OTROS USUARIOS: Comportamiento genérico
            pricelists_to_show.append(user_pricelist)
            # Agregar otras listas configuradas en el website si las hay
            if hasattr(website, 'sh_mayorista_pricelist_ids'):
                for pricelist in website.sh_mayorista_pricelist_ids:
                    if pricelist.id != user_pricelist.id and pricelist.active:
                        pricelists_to_show.append(pricelist)
            show_public_price = True
        
        # Calcular precios para cada lista seleccionada
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
        
        # Agregar precio público si corresponde y es diferente
        if show_public_price and public_price > 0:
            # Verificar que el precio público es diferente a los ya calculados
            user_price = prices_found.get(user_pricelist.id, 0)
            
            # Solo agregar si hay diferencia significativa
            if not user_price or abs(public_price - user_price) > 0.01:
                results.append({
                    'name': 'Público',  # Etiqueta para el list_price
                    'price': public_price,
                    'is_user_pricelist': False,
                    'pricelist_id': -1,  # ID especial para precio público
                })
        
        # Validación final: debe haber al menos 2 precios diferentes para mostrar etiquetas
        if len(results) <= 1:
            # Solo un precio o ninguno - no mostrar etiquetas comparativas
            if results:
                # Cambiar el nombre para no confundir
                results[0]['name'] = 'Precio'
            return results
        
        # Verificar que los precios son realmente diferentes
        unique_prices = set(r['price'] for r in results)
        if len(unique_prices) <= 1:
            # Todos los precios son iguales - simplificar
            return [{
                'name': 'Precio',
                'price': results[0]['price'],
                'is_user_pricelist': True,
                'pricelist_id': results[0]['pricelist_id'],
            }]
        
        # Ordenar resultados: precio del usuario primero, luego por valor
        results.sort(key=lambda x: (not x['is_user_pricelist'], x['price']))
        
        # Logging para debug (solo si está habilitado)
        import logging
        _logger = logging.getLogger(__name__)
        if _logger.isEnabledFor(logging.DEBUG):
            _logger.debug("="*50)
            _logger.debug(f"get_comparative_prices para: {self.name}")
            _logger.debug(f"Usuario: {user.name} | Lista: {user_pricelist.name}")
            _logger.debug(f"Precio público (list_price): ${public_price:.2f}")
            _logger.debug(f"Listas evaluadas: {[pl.name for pl in pricelists_to_show]}")
            _logger.debug("Precios calculados:")
            for pl_id, price in prices_found.items():
                pl = self.env['product.pricelist'].browse(pl_id)
                _logger.debug(f"  - {pl.name}: ${price:.2f}")
            _logger.debug("Resultados finales:")
            for r in results:
                usuario_tag = " [USUARIO]" if r['is_user_pricelist'] else ""
                _logger.debug(f"  - {r['name']}: ${r['price']:.2f}{usuario_tag}")
            _logger.debug("="*50)
        
        return results