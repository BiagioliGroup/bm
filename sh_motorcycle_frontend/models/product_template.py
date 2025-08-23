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
        Obtiene precios comparativos para mostrar en tienda
        VERSIÓN FINAL CORREGIDA: Soluciona todos los problemas identificados
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
                user_partner = current_user.partner_id.sudo()
                user_pricelist = user_partner.property_product_pricelist
            else:
                # Usuario interno: acceso normal
                user_partner = current_user.partner_id
                user_pricelist = user_partner.property_product_pricelist
                
        except Exception:
            # Si hay cualquier error de permisos, no mostrar comparativos
            return []
        
        if not user_pricelist:
            return []
        
        # OBTENER LISTAS DE PRECIOS PARA COMPARAR
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
                ], limit=3)
                pricelists_to_check.extend(important_pricelists)
                
        except Exception:
            # Error accediendo a configuraciones - continuar solo con la pricelist del usuario
            pricelists_to_check = []
        
        # SIEMPRE agregar la pricelist del usuario (es la MÁS IMPORTANTE)
        if user_pricelist not in pricelists_to_check:
            pricelists_to_check.append(user_pricelist)
        
        # CALCULAR PRECIOS USANDO PARTNER NEUTRO
        # SOLUCIÓN: Crear un partner neutro genérico para cálculos
        try:
            # Buscar un partner público/genérico para cálculos neutrales
            public_partner = self.env['res.partner'].search([
                ('is_company', '=', False),
                ('supplier_rank', '=', 0),
                ('customer_rank', '>', 0)
            ], limit=1)
            
            # Si no hay partner público, crear uno temporal
            if not public_partner:
                public_partner = self.env['res.partner'].create({
                    'name': 'Precio Público Genérico',
                    'is_company': False,
                    'customer_rank': 1
                })
                
        except Exception:
            # Fallback: usar partner base del sistema
            public_partner = self.env['res.partner'].browse(1)
        
        results = []
        prices_found = {}  # {pricelist_id: price}
        
        for pricelist in pricelists_to_check:
            try:
                # CLAVE: Usar partner específico según el tipo de lista
                if pricelist.id == user_pricelist.id:
                    # Para la lista del usuario: usar su partner (para precios personalizados)
                    calc_partner = user_partner
                else:
                    # Para otras listas: usar partner neutro (para precios estándar)
                    calc_partner = public_partner
                
                # USAR SUDO() para calcular precios
                pricelist_sudo = pricelist.sudo()
                
                price = pricelist_sudo._get_product_price(
                    product_variant, 1.0, calc_partner, date=False, uom_id=product_variant.uom_id.id
                )
                
                # Solo agregar si el precio es válido y diferente
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
        
        # LÍMITE: Máximo 3 precios para evitar saturar la interfaz
        MAX_PRICES = 3
        if len(results) > MAX_PRICES:
            # Mantener: precio del usuario + los 2 más relevantes
            user_results = [r for r in results if r['is_user_pricelist']]
            other_results = [r for r in results if not r['is_user_pricelist']][:MAX_PRICES-1]
            results = user_results + other_results
        
        return results