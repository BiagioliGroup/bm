# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo.http import request
from odoo import http
from itertools import product as cartesian_product
from collections import defaultdict
from odoo.addons.website_sale.controllers.main import WebsiteSale
import logging
_logger = logging.getLogger(__name__)


class MotorCycleWebsiteSale(WebsiteSale):
    _sh_motorcycle_frontend_detail = {}

    def _prepare_product_values(self, product, category, search, **kwargs):
        """
            REPLACE/OVERWRITE METHOD BY SOFTHEALER
            to get vehicles and common products
        """
        
        values = super(MotorCycleWebsiteSale, self)._prepare_product_values(
            product, category, search, **kwargs)

        vehicles = request.env['motorcycle.motorcycle']
        vehicles_ids = []
        sh_is_common_product = False
        if product and product.product_variant_id:
            sh_is_common_product = product.product_variant_id.sh_is_common_product

        if product and product.product_variant_ids:
            for product_variant in product.product_variant_ids:
                if product_variant.motorcycle_ids:
                    vehicles_ids += product_variant.motorcycle_ids.ids
            vehicles_ids = list(set(vehicles_ids))
            vehicles = vehicles.browse(vehicles_ids).sorted(
                key=lambda r: r.make_id.id or 0)

        values['vehicles'] = vehicles
        values['sh_is_common_product'] = sh_is_common_product

        values['default_code'] = product.default_code

        return values
    
    def _get_motorcycle_context_from_details(self, details):
        motorcycle_type = details[0].get('motorcycle_type')
        motorcycle_make = details[0].get('motorcycle_make')
        motorcycle_model = details[0].get('motorcycle_model')
        motorcycle_year = details[0].get('motorcycle_year')

        motorcycle_heading = ''

        if all([motorcycle_type, motorcycle_make, motorcycle_model, motorcycle_year]):
            try:
                type_obj = request.env['motorcycle.type'].browse(int(motorcycle_type))
                make_obj = request.env['motorcycle.make'].browse(int(motorcycle_make))
                model_obj = request.env['motorcycle.mmodel'].browse(int(motorcycle_model))
                motorcycle_heading = f"{type_obj.name} - {make_obj.name} {model_obj.name} {motorcycle_year}"
                _logger.info(f"[🚀 Motorcycle Selected de _get_motorcycle_context_from_details] {motorcycle_heading}")
            except Exception as e:
                _logger.warning(f"[⚠️ Error generating motorcycle_heading] {e}")
                motorcycle_heading = ''

        return {
            'motorcycle_type': motorcycle_type or '',
            'motorcycle_make': motorcycle_make or '',
            'motorcycle_model': motorcycle_model or '',
            'motorcycle_year': motorcycle_year or '',
            'type_list': details[0].get('type_list', ''),
            'make_list': details[0].get('make_list', ''),
            'model_list': details[0].get('model_list', ''),
            'year_list': details[0].get('year_list', ''),
            'motorcycle_heading': motorcycle_heading,
        }

    def _shop_lookup_products(self, attrib_set, options, post, search, website):
        _logger.info(
            "[🔎 _shop_lookup_products] ENTER options=%s, post=%s, search=%r",
            options, post, search
        )

        # Llamada original al método fuzzy
        product_count, details, fuzzy_search_term = website._search_with_fuzzy(
            "products_only", search,
            limit=None,
            order=self._get_search_order(post),
            options=options
        )

        search_result = details[0].get('results', request.env['product.template'])\
                                     .with_context(bin_size=True)

        _logger.info(
            "[🔎 _shop_lookup_products] fuzzy='%s', count=%s, result_ids=%s",
            fuzzy_search_term, product_count, search_result.ids
        )

        # Extraemos el contexto motero
        motorcycle_type  = details[0].get('motorcycle_type')
        motorcycle_make  = details[0].get('motorcycle_make')
        motorcycle_model = details[0].get('motorcycle_model')
        motorcycle_year  = details[0].get('motorcycle_year')

        motorcycle_heading = ''
        if all([motorcycle_type, motorcycle_make, motorcycle_model, motorcycle_year]):
            try:
                type_obj  = request.env['motorcycle.type'].browse(int(motorcycle_type))
                make_obj  = request.env['motorcycle.make'].browse(int(motorcycle_make))
                model_obj = request.env['motorcycle.mmodel'].browse(int(motorcycle_model))
                motorcycle_heading = (
                    f"{type_obj.name} - {make_obj.name} "
                    f"{model_obj.name} {motorcycle_year}"
                )
                _logger.info(
                    "[🚀 _shop_lookup_products] motorcycle_heading=%r",
                    motorcycle_heading
                )
            except Exception as e:
                _logger.warning(
                    "[⚠️ _shop_lookup_products] Error generating heading: %s", e
                )

        # Guardamos el contexto extendido
        self._sh_motorcycle_frontend_detail = {
            'motorcycle_type': motorcycle_type or '',
            'motorcycle_make': motorcycle_make or '',
            'motorcycle_model': motorcycle_model or '',
            'motorcycle_year': motorcycle_year or '',
            'type_list':   details[0].get('type_list',   []),
            'make_list':   details[0].get('make_list',   []),
            'model_list':  details[0].get('model_list',  []),
            'year_list':   details[0].get('year_list',   []),
            'motorcycle_heading': motorcycle_heading,
        }

        _logger.info(
            "[🔎 _shop_lookup_products] context saved: %s",
            self._sh_motorcycle_frontend_detail
        )

        # Filtrado por atributos (sin cambios)
        if attrib_set:
            attribute_values = request.env['product.attribute.value'].browse(attrib_set)
            values_per_attribute = defaultdict(lambda: request.env['product.attribute.value'])
            multi_value_attribute = False
            for value in attribute_values:
                values_per_attribute[value.attribute_id] |= value
                if len(values_per_attribute[value.attribute_id]) > 1:
                    multi_value_attribute = True

            def filter_template(template, attribute_values_list):
                attribute_value_to_ptav = {
                    ptav.product_attribute_value_id: ptav.id
                    for ptav in template.attribute_line_ids.product_template_value_ids
                }
                possible_combinations = False
                for attribute_values in attribute_values_list:
                    ptavs = request.env['product.template.attribute.value'].browse(
                        [attribute_value_to_ptav[val] for val in attribute_values if val in attribute_value_to_ptav]
                    )
                    if len(ptavs) < len(attribute_values):
                        continue
                    if len(ptavs) == len(template.attribute_line_ids):
                        if template._is_combination_possible(ptavs):
                            return True
                    elif len(ptavs) < len(template.attribute_line_ids):
                        if len(attribute_values_list) == 1:
                            if any(template._get_possible_combinations(necessary_values=ptavs)):
                                return True
                        if not possible_combinations:
                            possible_combinations = template._get_possible_combinations()
                        if any(len(ptavs & combination) == len(ptavs) for combination in possible_combinations):
                            return True
                return False

            if not multi_value_attribute:
                possible_attrib_values_list = [attribute_values]
            else:
                possible_attrib_values_list = [
                    request.env['product.attribute.value'].browse([v.id for v in values])
                    for values in cartesian_product(*values_per_attribute.values())
                ]

            search_result = search_result.filtered(
                lambda tmpl: filter_template(tmpl, possible_attrib_values_list)
            )
            _logger.info(
                "[🔎 _shop_lookup_products] after attribute filter, ids=%s",
                search_result.ids
            )

        _logger.info("[🔎 _shop_lookup_products] RETURNING")
        return fuzzy_search_term, product_count, search_result



    def _get_search_options(
            self, category=None, attrib_values=None, pricelist=None, min_price=0.0, max_price=0.0, conversion_rate=1, **post):
        """
            INHERITED BY SOFTHEALER
            Get type, make, mode, year values from URL/POST and add it into options in order to use it in
            1) _shop_lookup_products in website_sale controller
            2) _search_get_detail in product template
        """
        result = super(MotorCycleWebsiteSale, self)._get_search_options(
            category=category, attrib_values=attrib_values, pricelist=pricelist, min_price=min_price, max_price=max_price, conversion_rate=conversion_rate, **post
        )
        options_motorcycle = {
            'type': post.get('type', False),
            'make': post.get('make', False),
            'model': post.get('model', False),
            'year': post.get('year', False),
        }
        _logger.info("[🔍 _get_search_options] post params: %s", post)
        _logger.info("[🔍 _get_search_options] options built: %s", result)
        result.update(options_motorcycle)
        return result

    def _shop_get_query_url_kwargs(self,category , search, min_price, max_price, **post):
        """
            INHERITED BY SOFTHEALER
            Get type, make, mode, year values from URL/POST and add it into KEEP in order to keep
            all the parameter when user click on category, attribute or price.
        """
        result = super(MotorCycleWebsiteSale, self)._shop_get_query_url_kwargs(
            category , search, min_price, max_price, **post)
        options_motorcycle = {}
        if post.get('type', False):
            options_motorcycle.update({
                'type': post.get('type', False)
            })
        if post.get('make', False):
            options_motorcycle.update({
                'make': post.get('make', False)
            })
        if post.get('model', False):
            options_motorcycle.update({
                'model': post.get('model', False)
            })
        if post.get('year', False):
            options_motorcycle.update({
                'year': post.get('year', False)
            })
        result.update(options_motorcycle)
        return result


    @http.route()
    def shop(self, page=0, category=None, search='', min_price=0.0, max_price=0.0, ppg=False, **post):
        # Ejecutamos primero la lógica de búsqueda y contexto
        fuzzy, count, products = self._shop_lookup_products(
            attrib_set=None,
            options=self._get_search_options(**request.params),  # ✅ aquí va solo esto
            post=request.params,
            search=search,
            website=request.website
        )

        moto_context = self._sh_motorcycle_frontend_detail.copy()
        moto_context.update({
            'filter_order': getattr(request.website, 'sh_filter_order', False),
            'show_only_with_products': getattr(request.website, 'sh_show_only_with_products', False),
        })
        
        _logger.info("🔧 filter_order=%s, show_only_with_products=%s", 
                 moto_context['filter_order'], moto_context['show_only_with_products'])

        request.update_context(**moto_context)

        res = super(MotorCycleWebsiteSale, self).shop(
            page, category, search, min_price, max_price, ppg, **post
        )

        if hasattr(res, 'qcontext'):
            res.qcontext.update(moto_context)

        return res






class sh_motorcycle(http.Controller):

    @http.route(['/sh_motorcycle/get_type_list'], type='json', auth='public', website=True)
    def get_type_list(self):
        """
            METHOD BY SOFTHEALER
            to get vehicle type
        """
        type_list = request.env['motorcycle.type'].sudo().search_read(
            domain=[],
            fields=['id', 'name'],
            order="id asc",
        )
        return type_list or []

    @http.route(['/sh_motorcycle/get_make_list'], type='json', auth='public', website=True)
    def get_make_list(self, type_id=None):
        """
            METHOD BY SOFTHEALER
            to get vehicle make
        """
        default_make_list = []
        make_list = []
        if not type_id:
            default_make_list = request.env['motorcycle.make'].sudo().search_read(
                domain=[],
                fields=['id', 'name'],
                order="id asc",
            )

        if type_id not in ('', "", None, False):
            if type_id != int:
                type_id = int(type_id)
            search_make_list = request.env['motorcycle.mmodel'].sudo().search_read(
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

        if not make_list:
            return default_make_list or []

        return make_list or []

    @http.route(['/sh_motorcycle/get_year_list'], type='json', auth='public', website=True)
    def get_year_list(self, type_id=None, make_id=None):
        """
            CORREGIDO: Get vehicle year based only on type and make
        """
        year_list = []
        if (
            type_id not in ('', None, False) and
            make_id not in ('', None, False)
        ):
            try:
                type_id = int(type_id)
                make_id = int(make_id)
                
                vehicles = request.env['motorcycle.motorcycle'].sudo().search([
                    ('type_id', '=', type_id),
                    ('make_id', '=', make_id),
                ])

                year_list = list(set(vehicle.year for vehicle in vehicles))
                year_list.sort(reverse=True)
            except ValueError:
                pass
        return year_list or []

    @http.route(['/sh_motorcycle/get_model_list'], type='json', auth='public', website=True)
    def get_model_list(self, type_id=None, make_id=None, year=None):
        """
            MODIFICADO: ahora filtra también por Año.
        """
        model_list = []
        if (
            type_id not in ('', "", None, False) and
            make_id not in ('', "", None, False) and
            year not in ('', "", None, False)
        ):
            try:
                type_id = int(type_id)
                make_id = int(make_id)
                year = int(year)

                # Ahora buscamos las motos específicas para tipo+marca+año
                motorcycles = request.env['motorcycle.motorcycle'].sudo().search([
                    ('type_id', '=', type_id),
                    ('make_id', '=', make_id),
                    ('year', '=', year),
                ])

                # Extraemos los modelos de esas motos
                model_ids = motorcycles.mapped('mmodel_id').filtered(lambda m: m.id)

                # Eliminamos duplicados
                model_list = [{'id': model.id, 'name': model.name} for model in model_ids.sorted(key=lambda m: m.name)]
            except ValueError:
                pass

        return model_list or []

    @http.route(['/sh_motorcycle/is_bike_already_in_garage'], type='json', auth='public', website=True)
    def is_bike_already_in_garage(self, type_id=None, make_id=None, model_id=None, year=None):
        """
            METHOD BY SOFTHEALER
            to check vehicle is already in garage or not
        """
        is_already = False

        if (
            request.session.uid and
            type_id not in ('', "", None, False) and
            make_id not in ('', "", None, False) and
            model_id not in ('', "", None, False) and
            year not in ('', "", None, False)
        ):
            try:
                type_id = int(type_id)
                make_id = int(make_id)
                model_id = int(model_id)
                year = int(year)

                search_motorcycle = request.env['motorcycle.garage'].sudo().search([
                    ('type_id', '=', type_id),
                    ('make_id', '=', make_id),
                    ('mmodel_id', '=', model_id),
                    ('year', '=', year),
                    ('user_id', '=', request.env.user.id)
                ], limit=1)

                is_already = bool(search_motorcycle)

            except ValueError:
                pass

        return {
            'is_bike_already_in_garage': is_already
        }

    @http.route(['/sh_motorcycle/add_bike_to_garage'], type='json', auth='public', website=True)
    def add_bike_to_garage(self, type_id=None, make_id=None, model_id=None, year=None):
        """
            METHOD BY SOFTHEALER
            to add vehicle to garage option
        """
        search_motorcycle = False
        if (
            request.env.user and
            type_id not in ('', "", None, False) and
            make_id not in ('', "", None, False) and
            model_id not in ('', "", None, False) and
            year not in ('', "", None, False)
        ):
            try:
                if type_id != int:
                    type_id = int(type_id)
                if make_id != int:
                    make_id = int(make_id)
                if model_id != int:
                    model_id = int(model_id)
                if year != int:
                    year = int(year)
                garage_obj = request.env['motorcycle.garage']
                search_motorcycle = garage_obj.sudo().search([
                    ('type_id', '=', type_id),
                    ('make_id', '=', make_id),
                    ('mmodel_id', '=', model_id),
                    ('year', '=', year),
                    ('user_id', '=', request.env.user.id)
                ], limit=1)
            except ValueError:
                pass

            if not search_motorcycle:
                garage_vals = {
                    'type_id': type_id,
                    'make_id': make_id,
                    'mmodel_id': model_id,
                    'year': year,
                    'user_id': request.env.user.id,
                }
                garage_obj.sudo().create(garage_vals)

        return {}

    def _prepare_garage_layout_values(self):
        """
            METHOD BY SOFTHEALER
            to prepare value for garage option
        """
        values = {}
        if request.env.user:
            garage_obj = request.env['motorcycle.garage']
            search_motorcycles = garage_obj.sudo().search([
                ('user_id', '=', request.env.user.id)
            ])
            values.update({
                'motorcycles': search_motorcycles,
            })
            return values

    @http.route(['/my/garage'], type='http', auth="user", website=True)
    def my_garage(self, **kw):
        """
            METHOD BY SOFTHEALER
            /my/garage custom url
        """
        values = self._prepare_garage_layout_values()
        return request.render("sh_motorcycle_frontend.sh_motorcycle_my_garage_tmpl", values)

    @http.route(['/my/garage/remove_bike'], type='http', auth="user", website=True)
    def remove_bike_from_my_garage(self, **kw):
        """
            METHOD BY SOFTHEALER
            to remove vehicle from garage option
        """
        garage_obj = request.env['motorcycle.garage']
        if kw and kw.get('id', False) and request.env.user:
            id = kw.get('id')
            if id != int:
                id = int(id)
            search_motorcycles = garage_obj.sudo().search([
                ('id', '=', id),
                ('user_id', '=', request.env.user.id)
            ])
            if (
                search_motorcycles and
                search_motorcycles.user_id and
                search_motorcycles.user_id.id == request.env.user.id
            ):
                search_motorcycles.sudo().unlink()
        return request.redirect('/my/garage')

    @http.route(['/sh_motorcycle/get_saved_bike'], type='json', auth='public', website=True)
    def get_saved_bike(self):
        """
            METHOD BY SOFTHEALER
            to save vehicle in garage option
        """
        saved_bike_list = []
        if request.env.user:
            garage_obj = request.env['motorcycle.garage']
            search_motorcycles = garage_obj.sudo().search([
                ('user_id', '=', request.env.user.id)
            ])
            if search_motorcycles:
                saved_bike_dic = {}
                for motorcycle in search_motorcycles:
                    moto_url = '/shop?type=' + str(motorcycle.type_id.id) + '&make=' + str(
                        motorcycle.make_id.id) + '&model=' + str(motorcycle.mmodel_id.id) + '&year=' + str(motorcycle.year)
                    saved_bike_dic.update({
                        motorcycle.id:
                            {
                                'id': motorcycle.id,
                                'name': motorcycle.name,
                                'moto_url': moto_url
                            }
                    })
                if saved_bike_dic:
                    for key, value in sorted(saved_bike_dic.items(), key=lambda kv: kv[1]['name']):
                        saved_bike_list.append(value)
        return saved_bike_list or []

    @http.route(['/sh_motorcycle/is_user_logined_in'], type='json', auth='public', website=True)
    def is_user_logined_in(self):
        """
            METHOD BY SOFTHEALER
            to check user is logged in or not
        """
        if request.session.uid:
            return {
                'is_user_logined_in': True,
                'sh_is_show_garage': request.website.sh_is_show_garage,

            }
        return {
            'is_user_logined_in': False,
            'sh_is_show_garage': request.website.sh_is_show_garage,
        }
