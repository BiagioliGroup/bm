# -*- coding: utf-8 -*-
# Sergio Biagioli Code

from odoo.http import request
from odoo import http
from odoo.addons.website_sale.controllers.main import WebsiteSale
import logging

_logger = logging.getLogger(__name__)


class BiagioliWebsiteSale(WebsiteSale):

    def _prepare_product_values(self, product, category, search, **kwargs):
        _logger.warning("🚨 Sergio DEBUG: Ejecutando _prepare_product_values para %s", product.display_name)

        values = super(BiagioliWebsiteSale, self)._prepare_product_values(
            product, category, search, **kwargs)

        qty = product.sudo().qty_available
        values['product_qty_display'] = "En stock" if qty > 0 else False

        _logger.warning("🚨 Sergio DEBUG: product_qty_display = %s", values['product_qty_display'])

        return values
    
    def product(self, product, category='', search='', **kwargs):
        _logger.warning("🚨 Sergio DEBUG: Entrando al método `product()` de BiagioliWebsiteSale")
        return super().product(product, category, search, **kwargs)

