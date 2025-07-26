# -*- coding: utf-8 -*-
# Sergio Biagioli Code

from odoo.http import request
from odoo import http
from odoo.addons.website_sale.controllers.main import WebsiteSale
import logging

_logger = logging.getLogger(__name__)


class BiagioliWebsiteSale(WebsiteSale):

    """ Este método se ejecuta cuando se carga el grid de productos y ODOO lo brinda justo antes de renderizar el QWeb. 
    Para que el QWeb pueda acceder a los valores que le pasamos, debemos devolverlos en el diccionario `values`"""

    def _get_additional_shop_values(self, values):
        # Log para comprobar que entró al hook
        products = values.get('products') or request.env['product.template']
        _logger.warning("🚨 Sergio DEBUG: _get_additional_shop_values called for products %s", products.ids)

        qty_data = products.sudo().read(['id', 'qty_available'])
        qty_map = {d['id']: d['qty_available'] for d in qty_data}
        _logger.warning("🚨 Sergio DEBUG: built qty_map with %s entries", len(qty_map))
        return {'products_qty_map': qty_map}



    """ este metodo sirve para pagina de producto INDIVIDUAL """

    # def _prepare_product_values(self, product, category, search, **kwargs):

    #     values = super(BiagioliWebsiteSale, self)._prepare_product_values(
    #         product, category, search, **kwargs)


    #     return values
    
