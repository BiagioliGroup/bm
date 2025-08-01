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
        Solo muestra comparativos cuando hay múltiples listas de precios diferentes
        Y que realmente tengan precios específicos configurados para el producto
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

        results = []
        base_price = self.list_price  # Precio base del producto
        prices_found = set()
        
        # Agregar las listas configuradas en settings
        if hasattr(website, 'sh_mayorista_pricelist_ids'):
            for pricelist in website.sh_mayorista_pricelist_ids:
                try:
                    price = pricelist._get_product_price(self, 1.0, partner)
                    
                    # VALIDACIÓN CRÍTICA: Solo agregar si el precio es diferente al precio base
                    # Esto evita mostrar precios cuando la lista usa reglas sobre productos sin precio mayorista
                    if abs(price - base_price) > 0.01:  # Tolerancia para diferencias mínimas
                        # Verificar si este pricelist tiene reglas específicas para este producto
                        # o si está aplicando reglas por defecto sobre un precio inexistente
                        pricelist_items = self.env['product.pricelist.item'].search([
                            ('pricelist_id', '=', pricelist.id),
                            '|',
                            ('product_tmpl_id', '=', self.id),
                            ('product_id', 'in', self.product_variant_ids.ids)
                        ])
                        
                        # Solo agregar si hay items específicos o si el precio es significativamente diferente
                        if pricelist_items or abs(price - base_price) > (base_price * 0.05):  # 5% de diferencia mínima
                            if price not in prices_found:
                                results.append({
                                    'name': pricelist.name,
                                    'price': price,
                                    'is_user_pricelist': pricelist.id == user_pricelist.id,
                                    'pricelist_id': pricelist.id,
                                })
                                prices_found.add(price)
                except:
                    # Si hay error calculando precio, saltear esta lista
                    continue
        
        # Asegurar que la lista del usuario esté incluida solo si es diferente
        if user_pricelist.id not in [r['pricelist_id'] for r in results]:
            try:
                price = user_pricelist._get_product_price(self, 1.0, partner)
                
                # Solo agregar la lista del usuario si tiene un precio diferente al base
                if abs(price - base_price) > 0.01:
                    # Verificar si tiene reglas específicas
                    user_pricelist_items = self.env['product.pricelist.item'].search([
                        ('pricelist_id', '=', user_pricelist.id),
                        '|',
                        ('product_tmpl_id', '=', self.id),
                        ('product_id', 'in', self.product_variant_ids.ids)
                    ])
                    
                    if user_pricelist_items or abs(price - base_price) > (base_price * 0.05):
                        if price not in prices_found:
                            results.append({
                                'name': user_pricelist.name,
                                'price': price,
                                'is_user_pricelist': True,
                                'pricelist_id': user_pricelist.id,
                            })
                            prices_found.add(price)
                elif len(results) == 0:
                    # Si no hay otros precios diferentes, no mostrar nada
                    return []
            except:
                # Si hay error, no agregar
                pass
        
        # Solo devolver resultados si hay más de un precio REALMENTE diferente
        if len(results) <= 1:
            return []
        
        # Ordenar: precio del usuario primero, luego por precio ascendente
        results.sort(key=lambda x: (not x['is_user_pricelist'], x['price']))
        
        return results