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
            Metodo de Sergio Biagioli para obtener ciertos atributos que quiero mostrar 
            en el GRID del SHOP
        """
        # Llamamos al método original para mantener el comportamiento estándar
        values = super(BiagioliWebsiteSale, self)._prepare_product_values(
            product, category, search, **kwargs)

        # Añadimos el código interno del producto (default_code)
        values['default_code'] = product.default_code

        # Añadimos la cantidad on hand
        # values['qty_available'] = product.sudo().qty_available


        return values
