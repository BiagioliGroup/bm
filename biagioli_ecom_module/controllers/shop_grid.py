# -*- coding: utf-8 -*-
# Sergio Biagioli Code

from odoo.http import request
from odoo import http
from odoo.addons.website_sale.controllers.main import WebsiteSale
import logging

_logger = logging.getLogger(__name__)


class BiagioliWebsiteSale(WebsiteSale):

    def _prepare_product_values(self, product, category, search, **kwargs):
        """
            Metodo de Sergio Biagioli para mostrar atributos extra en la vista de producto (/shop/product)
        """
        values = super(BiagioliWebsiteSale, self)._prepare_product_values(
            product, category, search, **kwargs)

        values['default_code'] = product.default_code

        qty = product.sudo().qty_available
        values['product_qty_display'] = "En stock" if qty > 0 else False

        return values
