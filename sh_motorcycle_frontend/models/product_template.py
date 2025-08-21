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
        Funciona para todos los casos: Revendedor, Mayorista y Dropshipping
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

        # Obtener el producto variant principal para cálculos de precio
        product_variant = self.sudo().product_variant_ids[0] if self.sudo().product_variant_ids else None
        if not product_variant:
            return []
        
        results = []
        prices_found = {}  # {pricelist_id: price}
        list_price = self.list_price  # Precio público base
        
        # VALIDACIÓN ESPECIAL PARA DROPSHIPPING - ANTES de calcular cualquier cosa
        if user_pricelist.name and 'dropshipping' in user_pricelist.name.lower():
            # Buscar la lista mayorista específicamente
            mayorista_pricelist = None
            if hasattr(website, 'sh_mayorista_pricelist_ids'):
                for pricelist in website.sudo().sh_mayorista_pricelist_ids:
                    if 'mayorista' in pricelist.name.lower():
                        mayorista_pricelist = pricelist
                        break
            
            # Si no encontramos lista mayorista en configuración, buscar por nombre
            if not mayorista_pricelist:
                mayorista_pricelist = self.env['product.pricelist'].search([
                    ('name', 'ilike', 'mayorista')
                ], limit=1)
            
            # Verificar que el producto REALMENTE tiene precio mayorista configurado
            if mayorista_pricelist:
                try:
                    mayorista_price = mayorista_pricelist._get_product_price(
                        product_variant, 1.0, partner, date=False, uom_id=product_variant.uom_id.id
                    )
                    
                    # CRÍTICO: Verificar que el precio mayorista ES DIFERENTE al precio público
                    # Si son iguales, significa que no hay precio mayorista real configurado
                    if abs(mayorista_price - list_price) <= (list_price * 0.001):  # Tolerancia muy pequeña
                        # No hay precio mayorista real - no mostrar comparativos
                        return []
                        
                except Exception:
                    # Error calculando precio mayorista - no mostrar comparativos
                    return []
            else:
                # No hay lista mayorista - no mostrar comparativos para dropshipping
                return []
        
        # Lista de pricelists a evaluar (SIN duplicar la del usuario)
        pricelists_to_check = []
        
        # Agregar las listas configuradas en settings
        if hasattr(website, 'sh_mayorista_pricelist_ids'):
            for pricelist in website.sudo().sh_mayorista_pricelist_ids:
                if pricelist.id != user_pricelist.id:  # Evitar duplicados
                    pricelists_to_check.append(pricelist)
        
        # SIEMPRE agregar la lista del usuario
        pricelists_to_check.append(user_pricelist)
        
        # Calcular precios para cada lista
        for pricelist in pricelists_to_check:
            try:
                # Usar el método correcto de Odoo para obtener el precio
                price = pricelist._get_product_price(
                    product_variant, 
                    1.0, 
                    partner,
                    date=False,
                    uom_id=product_variant.uom_id.id
                )
                
                # Agregar el precio si es válido
                if price > 0:
                    prices_found[pricelist.id] = price
                    results.append({
                        'name': pricelist.name,
                        'price': price,
                        'is_user_pricelist': pricelist.id == user_pricelist.id,
                        'pricelist_id': pricelist.id,
                    })
                    
            except Exception as e:
                import logging
                _logger = logging.getLogger(__name__)
                _logger.warning(f"Error calculando precio para pricelist {pricelist.name}: {e}")
                continue
        
        # Solo mostrar si hay al menos 2 precios DIFERENTES
        unique_prices = set(prices_found.values())
        if len(unique_prices) <= 1:
            return []
        
        # Verificar que las diferencias son mínimamente significativas
        min_price = min(unique_prices)
        max_price = max(unique_prices)
        
        if min_price > 0 and ((max_price - min_price) / min_price) < 0.005:  # 0.5%
            return []
        
        # Ordenar: precio del usuario primero, luego por precio ascendente  
        results.sort(key=lambda x: (not x['is_user_pricelist'], x['price']))
        
        return results