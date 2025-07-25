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

        # Código interno
        values['default_code'] = product.default_code

        # Cantidad on hand real (con sudo, pero no la mostrarás directamente)
        real_qty = product.sudo().qty_available
        values['qty_available'] = real_qty

        # Cantidad para mostrar en el frontend (string separada)
        if real_qty <= 0:
            values['qty_display'] = False
        
        else:
            values['qty_display'] = "En stock"

        return values
