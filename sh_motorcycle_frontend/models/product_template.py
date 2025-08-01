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
        prices_found = set()  # Para evitar duplicados de precios
        
        # Agregar las listas configuradas en settings
        if hasattr(website, 'sh_mayorista_pricelist_ids'):
            for pricelist in website.sh_mayorista_pricelist_ids:
                try:
                    price = pricelist._get_product_price(self, 1.0, partner)
                    # Solo agregar si el precio es diferente a los ya encontrados
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
        
        # Asegurar que la lista del usuario esté incluida
        if user_pricelist.id not in [r['pricelist_id'] for r in results]:
            try:
                price = user_pricelist._get_product_price(self, 1.0, partner)
                # Solo agregar si es un precio diferente
                if price not in prices_found:
                    results.append({
                        'name': user_pricelist.name,
                        'price': price,
                        'is_user_pricelist': True,
                        'pricelist_id': user_pricelist.id,
                    })
                    prices_found.add(price)
                elif len(results) == 0:
                    # Si no hay otros precios, agregar el del usuario de todos modos
                    results.append({
                        'name': user_pricelist.name,
                        'price': price,
                        'is_user_pricelist': True,
                        'pricelist_id': user_pricelist.id,
                    })
            except:
                # Si hay error, no agregar
                pass
        
        # Solo devolver resultados si hay más de un precio diferente
        # O si hay múltiples listas (aunque tengan el mismo precio)
        if len(results) <= 1 and len(prices_found) <= 1:
            return []
            
        # Ordenar: precio del usuario primero, luego por precio ascendente
        results.sort(key=lambda x: (not x['is_user_pricelist'], x['price']))
        
        return results
    
    def is_user_mayorista(self):
        """
        Verifica si el usuario actual es mayorista
        """
        user = self.env.user
        if not user or user._is_public():
            return False
            
        partner = user.partner_id
        pricelist = partner.property_product_pricelist
        
        # Verificar si tiene una lista que contenga "mayorista" en el nombre (case insensitive)
        if pricelist and 'mayorista' in pricelist.name.lower():
            return True
            
        return False

    @api.model
    def _search_get_detail(self, website, order, options):
        """
            INHERITED BY SOFTHEALER
            ==> In order to add vehicle domain in base_domain and return
                - motorcycle_heading,
                - motorcycle_type,
                - motorcycle_make
                - motorcycle_model
                - motorcycle_year
                - type_list
                - make_list
                - model_list
                - year_list

        """

        result = super(ProductTemplate, self)._search_get_detail(
            website, order, options)
        base_domain = result.get('base_domain', [])
        keep_vehicle = True
        category = options.get('category')
        min_price = options.get('min_price')
        max_price = options.get('max_price')
        attrib_values = options.get('attrib_values')
        if website:
            if category and website.sh_do_not_consider_vehicle_over_category:
                keep_vehicle = False

            if attrib_values and website.sh_do_not_consider_vehicle_over_attribute:
                keep_vehicle = False

            if min_price or max_price:
                if website.sh_do_not_consider_vehicle_over_price:
                    keep_vehicle = False

        # --------------------------------------------------------------------
        # softhealer custom code start here
        # --------------------------------------------------------------------
        base_domain = base_domain or []
        motorcycle_heading = False
        type_id = False
        make_id = False
        mmodel_id = False
        year = False

        type_list = []
        make_list = []
        model_list = []
        year_list = []

        search_motorcycles = False
        if (
            keep_vehicle and
            options and
            options.get('type', False) and
            options.get('make', False) and
            options.get('model', False) and
            options.get('year', False)
        ):

            type_id = options.get('type')
            make_id = options.get('make')
            mmodel_id = options.get('model')
            year = options.get('year')

            try:
                if type(type_id) != int:
                    type_id = int(type_id)
                if type(make_id) != int:
                    make_id = int(make_id)
                if type(mmodel_id) != int:
                    mmodel_id = int(mmodel_id)
                if type(year) != int:
                    year = int(year)

                vehicle_domain = [
                    ('type_id', '=', type_id),
                    ('make_id', '=', make_id),
                    ('mmodel_id', '=', mmodel_id),
                    ('year', '=', year),  # <- Verificar que la condición es correcta
                ]
                _logger.info(f"Searching motorcycles with: {vehicle_domain}")
                search_motorcycles = self.env['motorcycle.motorcycle'].sudo().search(vehicle_domain)
                

                # =========================================================
                # Type, Make, Model, Year selected when page refresh.

                type_list = self._get_type_list()
                make_list = self._get_make_list(type_id)
                model_list = self._get_model_list(type_id, make_id)
                year_list = self._get_year_list(type_id, make_id, mmodel_id)

                # =========================================================

            except ValueError:
                pass

            product_tmpl_id_list = []
            is_compute_vehicle_name = True
            if search_motorcycles:
                for motorcycle in search_motorcycles:
                    if is_compute_vehicle_name:
                        # VEHICLE NAME
                        vehicle_name = ''
                        if motorcycle.make_id:
                            vehicle_name += motorcycle.make_id.name + ' '
                        if motorcycle.mmodel_id:
                            vehicle_name += motorcycle.mmodel_id.name + ' '
                        if motorcycle.year:
                            vehicle_name += str(motorcycle.year)
                        if vehicle_name == '':
                            vehicle_name = False
                        motorcycle_heading = vehicle_name
                        # VEHICLE NAME
                        is_compute_vehicle_name = False

                    if motorcycle.product_ids:
                        for product in motorcycle.product_ids:
                            if product.product_tmpl_id:
                                product_tmpl_id_list.append(
                                    product.product_tmpl_id.id)

                # ------------------
                # Universal Products
                universal_products = self.env['product.product'].search([
                    ('sh_is_common_product', '=', True)
                ])

                product_tmpl_id_list += universal_products.mapped(
                    'product_tmpl_id').ids
                # ------------------
                # Universal Products
            base_domain.append([('id', 'in', product_tmpl_id_list)])

        result.update({'base_domain': base_domain})
        result.update({
            'motorcycle_heading': motorcycle_heading,
            'motorcycle_type': type_id,
            'motorcycle_make': make_id,
            'motorcycle_model': mmodel_id,
            'motorcycle_year': year,
            'type_list': type_list,
            'make_list': make_list,
            'model_list': model_list,
            'year_list': year_list,
        })

        _logger.info(f"motorcycle_heading = {motorcycle_heading}")
        # --------------------------------------------------------------------
        # softhealer custom code ends here
        # --------------------------------------------------------------------
        return result