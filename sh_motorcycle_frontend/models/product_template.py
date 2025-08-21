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
        Obtiene precios comparativos REALES para mostrar en tienda
        SOLO muestra productos que tienen precios mayoristas configurados
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
        prices_found = {}
        
        # Lista de pricelists a evaluar
        pricelists_to_check = []
        
        # Agregar las listas configuradas en settings
        if hasattr(website, 'sh_mayorista_pricelist_ids'):
            for pricelist in website.sudo().sh_mayorista_pricelist_ids:
                if pricelist.id != user_pricelist.id:
                    pricelists_to_check.append(pricelist)
        
        # SIEMPRE agregar la lista del usuario
        pricelists_to_check.append(user_pricelist)
        
        # PASO 1: Verificar que el producto REALMENTE tiene reglas de precio diferentes
        base_price = product_sudo.list_price  # Precio público base
        has_real_pricing = False
        
        for pricelist in pricelists_to_check:
            try:
                # VERIFICAR si existe una regla ESPECÍFICA para este producto en esta lista
                pricelist_items = self.env['product.pricelist.item'].sudo().search([
                    ('pricelist_id', '=', pricelist.id),
                    '|', 
                    '&', ('applied_on', '=', '1_product'), ('product_tmpl_id', '=', self.id),
                    '|',
                    '&', ('applied_on', '=', '0_product_variant'), ('product_id', '=', product_variant.id),
                    '&', ('applied_on', '=', '2_product_category'), ('categ_id', 'in', self._get_product_category_ids())
                ])
                
                if pricelist_items:
                    # Hay reglas específicas - calcular precio
                    calculated_price = pricelist._compute_price_rule(
                        product_variant, 1.0, partner, date='2025-08-21'
                    )[product_variant.id][0]
                    
                    # Verificar que el precio es REALMENTE diferente (no solo aplicación de regla general)
                    if abs(calculated_price - base_price) > (base_price * 0.01):  # Diferencia > 1%
                        has_real_pricing = True
                        price_rounded = round(calculated_price, 2)
                        
                        # Evitar duplicados
                        if price_rounded not in prices_found.values():
                            prices_found[pricelist.id] = price_rounded
                            results.append({
                                'name': pricelist.name,
                                'price': price_rounded,
                                'pricelist_id': pricelist.id,
                                'is_user_pricelist': pricelist.id == user_pricelist.id
                            })
                            
            except Exception as e:
                # Si hay error de conversión de monedas, intentar método alternativo
                import logging
                _logger = logging.getLogger(__name__)
                _logger.warning(f"Error calculando precio para lista {pricelist.name}: {e}")
                
                # MÉTODO ALTERNATIVO: Verificar reglas sin calcular precio
                try:
                    pricelist_items = self.env['product.pricelist.item'].sudo().search([
                        ('pricelist_id', '=', pricelist.id),
                        '|', 
                        '&', ('applied_on', '=', '1_product'), ('product_tmpl_id', '=', self.id),
                        '|',
                        '&', ('applied_on', '=', '0_product_variant'), ('product_id', '=', product_variant.id),
                        '&', ('applied_on', '=', '2_product_category'), ('categ_id', 'in', self._get_product_category_ids())
                    ])
                    
                    if pricelist_items:
                        # Usar precio fijo de la regla si existe
                        fixed_price_item = pricelist_items.filtered(lambda x: x.compute_price == 'fixed')
                        if fixed_price_item:
                            fixed_price = fixed_price_item[0].fixed_price
                            if fixed_price > 0 and abs(fixed_price - base_price) > (base_price * 0.01):
                                has_real_pricing = True
                                price_rounded = round(fixed_price, 2)
                                
                                if price_rounded not in prices_found.values():
                                    prices_found[pricelist.id] = price_rounded
                                    results.append({
                                        'name': pricelist.name,
                                        'price': price_rounded,
                                        'pricelist_id': pricelist.id,
                                        'is_user_pricelist': pricelist.id == user_pricelist.id
                                    })
                except:
                    continue
        
        # PASO 2: Solo mostrar si hay precios REALES diferentes
        if not has_real_pricing:
            return []  # No hay precios mayoristas reales - mostrar precio público normal
        
        # Ordenar: precio del usuario primero, luego otros por precio
        results.sort(key=lambda x: (not x['is_user_pricelist'], x['price']))
        
        # Solo devolver si hay al menos 2 precios diferentes
        if len(results) >= 2:
            return results
        else:
            return []

    def _get_product_category_ids(self):
        """Helper method para obtener categorías del producto"""
        categories = []
        if self.categ_id:
            categories.append(self.categ_id.id)
            # Agregar categorías padre
            parent = self.categ_id.parent_id
            while parent:
                categories.append(parent.id)
                parent = parent.parent_id
        return categories