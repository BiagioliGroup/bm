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

    # REEMPLAZAR el método get_comparative_prices en sh_motorcycle_frontend/models/product_template.py

    def get_comparative_prices(self):
        """
        Obtiene precios comparativos para mostrar en tienda
        VERSIÓN BULLETPROOF - Evita problemas de conversión de monedas
        """
        self.ensure_one()
        user = self.env.user
        website = self.env['website'].get_current_website()
        
        # Si no está configurado, no mostrar precios comparativos
        if not hasattr(website, 'sh_show_comparative_prices') or not website.sh_show_comparative_prices:
            return []
            
        partner = user.partner_id
        user_pricelist = partner.property_product_pricelist
        
        if not user_pricelist:
            return []

        # CRÍTICO: Usar sudo() para obtener datos del producto
        product_sudo = self.sudo()
        product_variant = product_sudo.product_variant_ids[0] if product_sudo.product_variant_ids else None
        if not product_variant:
            return []
        
        results = []
        prices_found = {}  # {pricelist_id: price}
        
        # Lista de pricelists a evaluar (SIN duplicar la del usuario)
        pricelists_to_check = []
        
        # Agregar las listas configuradas en settings (usando sudo())
        if hasattr(website, 'sh_mayorista_pricelist_ids'):
            for pricelist in website.sudo().sh_mayorista_pricelist_ids:
                if pricelist.id != user_pricelist.id:  # Evitar duplicados
                    pricelists_to_check.append(pricelist)
        
        # SIEMPRE agregar la lista del usuario
        pricelists_to_check.append(user_pricelist)
        
        # Calcular precios para cada lista
        for pricelist in pricelists_to_check:
            try:
                # NUEVA ESTRATEGIA: Usar el contexto de pricelist directamente para evitar conversión
                price = product_variant.sudo().with_context(
                    pricelist=pricelist.id,
                    date='2025-08-21',
                    uom=product_variant.uom_id.id,
                    # CRÍTICO: Forzar misma moneda para evitar conversión
                    currency_id=self.env.company.currency_id.id
                ).price
                
                # Solo agregar si el precio es válido y diferente
                if price and price > 0:
                    # Verificar si ya tenemos este precio (evitar duplicados por precio)
                    price_rounded = round(price, 2)
                    duplicate_found = False
                    
                    for existing_price in prices_found.values():
                        if abs(existing_price - price_rounded) < 0.01:  # Tolerancia de centavos
                            duplicate_found = True
                            break
                    
                    if not duplicate_found:
                        prices_found[pricelist.id] = price_rounded
                        
                        results.append({
                            'name': pricelist.name,
                            'price': price_rounded,
                            'pricelist_id': pricelist.id,
                            'is_user_pricelist': pricelist.id == user_pricelist.id
                        })
                        
            except Exception as e:
                # ALTERNATIVA: Si falla, usar list_price como base
                import logging
                _logger = logging.getLogger(__name__)
                _logger.warning(f"Error calculando precio para lista {pricelist.name}: {e}")
                
                # Como fallback, usar el precio base del producto
                try:
                    base_price = product_sudo.list_price
                    if pricelist.name.lower() == 'mayorista':
                        # Aplicar descuento mayorista típico del 30%
                        fallback_price = base_price * 0.7
                    elif pricelist.name.lower() == 'publico':
                        fallback_price = base_price
                    else:
                        fallback_price = base_price * 0.8  # Descuento genérico
                    
                    if fallback_price > 0:
                        price_rounded = round(fallback_price, 2)
                        if price_rounded not in prices_found.values():
                            results.append({
                                'name': f"{pricelist.name} (aprox)",
                                'price': price_rounded,
                                'pricelist_id': pricelist.id,
                                'is_user_pricelist': pricelist.id == user_pricelist.id
                            })
                            prices_found[pricelist.id] = price_rounded
                except:
                    # Si todo falla, continuar con la siguiente lista
                    continue
        
        # Ordenar: precio del usuario primero, luego otros por precio ascendente
        results.sort(key=lambda x: (not x['is_user_pricelist'], x['price']))
        
        # Solo devolver si hay al menos 2 precios diferentes
        if len(results) >= 2:
            return results
        else:
            return []