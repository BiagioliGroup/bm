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



    # PARCHE PARA EL MÉTODO get_comparative_prices()
    # ARCHIVO: sh_motorcycle_frontend/models/product_template.py
    # REEMPLAZAR el método existente con esta versión corregida

    def get_comparative_prices(self):
        """
        Obtiene precios comparativos para mostrar en tienda
        VERSIÓN CORREGIDA: Maneja correctamente permisos para usuarios Portal
        """
        self.ensure_one()
        
        # Obtener contexto actual de forma segura
        current_user = self.env.user
        
        try:
            website = self.env['website'].get_current_website()
        except:
            # Fallback si no hay contexto de website
            website = self.env['website'].search([('company_id', '=', current_user.company_id.id)], limit=1)
        
        # Si no está configurado, no mostrar precios comparativos
        if not hasattr(website, 'sh_show_comparative_prices') or not website.sh_show_comparative_prices:
            return []
        
        # Para usuarios públicos, no mostrar nada
        if current_user._is_public():
            return []
        
        # Obtener el producto variant principal para cálculos de precio
        product_variant = self.product_variant_ids[0] if self.product_variant_ids else None
        if not product_variant:
            return []
        
        # MANEJO SEGURO DE PERMISOS PARA USUARIOS PORTAL
        try:
            # Verificar si el usuario es Portal
            is_portal_user = any(
                'portal' in group.name.lower() or group.name == 'Portal' 
                for group in current_user.groups_id
            )
            
            if is_portal_user:
                # Usuario Portal: usar sudo() para acceder a su propia pricelist
                # Esto es seguro porque solo accede a sus propios datos
                partner = current_user.partner_id.sudo()
                user_pricelist = partner.property_product_pricelist
            else:
                # Usuario interno: acceso normal
                partner = current_user.partner_id
                user_pricelist = partner.property_product_pricelist
                
        except Exception:
            # Si hay cualquier error de permisos, no mostrar comparativos
            return []
        
        if not user_pricelist:
            return []
        
        results = []
        prices_found = {}  # {pricelist_id: price}
        list_price = self.list_price  # Precio público base
        
        # VALIDACIÓN ESPECIAL PARA DROPSHIPPING
        if user_pricelist.name and 'dropshipping' in user_pricelist.name.lower():
            # Para Dropshipping, buscar mayorista usando sudo()
            try:
                mayorista_pricelist = None
                
                # Buscar mayorista en configuración del website (con sudo para usuarios portal)
                if hasattr(website, 'sh_mayorista_pricelist_ids') and website.sh_mayorista_pricelist_ids:
                    website_lists = website.sh_mayorista_pricelist_ids.sudo() if is_portal_user else website.sh_mayorista_pricelist_ids
                    for pricelist in website_lists:
                        if 'mayorista' in pricelist.name.lower():
                            mayorista_pricelist = pricelist
                            break
                
                # Si no encontramos lista mayorista en configuración, buscar por nombre
                if not mayorista_pricelist:
                    search_env = self.env['product.pricelist'].sudo() if is_portal_user else self.env['product.pricelist']
                    mayorista_pricelist = search_env.search([('name', 'ilike', 'mayorista')], limit=1)
                    
            except Exception:
                # Error accediendo a pricelists - no mostrar comparativos
                return []
            
            # Verificar que el producto REALMENTE tiene precio mayorista configurado
            if mayorista_pricelist:
                try:
                    mayorista_price = mayorista_pricelist.sudo()._get_product_price(
                        product_variant, 1.0, partner, date=False, uom_id=product_variant.uom_id.id
                    )
                    
                    # Verificar que el precio mayorista ES DIFERENTE al precio público
                    if abs(mayorista_price - list_price) <= (list_price * 0.001):
                        # No hay precio mayorista real - no mostrar comparativos
                        return []
                        
                except Exception:
                    # Error calculando precio mayorista - no mostrar comparativos
                    return []
            else:
                # No hay lista mayorista - no mostrar comparativos para dropshipping
                return []
        
        # OBTENER LISTAS DE PRECIOS PARA COMPARAR (CON SUDO PARA PORTALS)
        pricelists_to_check = []
        
        try:
            # Usar sudo() para que usuarios portal puedan acceder a configuraciones del website
            if hasattr(website, 'sh_mayorista_pricelist_ids') and website.sh_mayorista_pricelist_ids:
                website_lists = website.sh_mayorista_pricelist_ids.sudo() if is_portal_user else website.sh_mayorista_pricelist_ids
                pricelists_to_check.extend(website_lists)
            
            # Si no hay listas configuradas, buscar algunas listas importantes
            if not pricelists_to_check:
                search_env = self.env['product.pricelist'].sudo() if is_portal_user else self.env['product.pricelist']
                important_pricelists = search_env.search([
                    '|', '|',
                    ('name', 'ilike', 'mayorista'),
                    ('name', 'ilike', 'revendedor'),
                    ('name', 'ilike', 'publico')
                ], limit=4)
                pricelists_to_check.extend(important_pricelists)
                
        except Exception:
            # Error accediendo a configuraciones - continuar solo con la pricelist del usuario
            pricelists_to_check = []
        
        # Agregar la pricelist del usuario (siempre debe estar)
        if user_pricelist not in pricelists_to_check:
            pricelists_to_check.append(user_pricelist)
        
        # CALCULAR PRECIOS PARA CADA PRICELIST (CON SUDO PARA PORTALS)
        for pricelist in pricelists_to_check:
            try:
                # USAR SUDO() para calcular precios - esto es seguro porque:
                # 1. Solo calculamos precios de productos públicos
                # 2. No exponemos datos sensibles de otros usuarios
                # 3. Los precios son información que el usuario debe ver
                pricelist_sudo = pricelist.sudo()
                
                price = pricelist_sudo._get_product_price(
                    product_variant, 1.0, partner, date=False, uom_id=product_variant.uom_id.id
                )
                
                # Solo agregar si el precio es diferente y válido
                if price > 0 and pricelist.id not in prices_found:
                    prices_found[pricelist.id] = price
                    
                    results.append({
                        'pricelist_id': pricelist.id,
                        'name': pricelist.name,
                        'price': price,
                        'is_user_pricelist': pricelist.id == user_pricelist.id,
                        'formatted_price': '{:,.2f}'.format(price),
                    })
                    
            except Exception:
                # Error calculando precio específico - continuar con las demás
                continue
        
        # Ordenar: Pricelist del usuario primero, luego por precio
        results.sort(key=lambda x: (not x['is_user_pricelist'], x['price']))
        
        # Solo mostrar si hay más de una pricelist con precios diferentes
        unique_prices = set(prices_found.values())
        if len(unique_prices) <= 1:
            return []
        
        return results