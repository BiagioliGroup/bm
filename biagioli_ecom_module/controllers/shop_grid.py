# -*- coding: utf-8 -*-
# Sergio Biagioli Code

from odoo.addons.sh_motorcycle_frontend.controllers.sh_motorcycle_frontend import MotorCycleWebsiteSale
from odoo.http import request
from odoo import http
import logging


_logger = logging.getLogger(__name__)


class BiagioliWebsiteSale(MotorCycleWebsiteSale):

    """ Aqui es donde vamos a inyectar el stock de los productos en la pagina de shop y cualquier otro dato que queramos

        Gran Dato: DEPENDEMOS DE sh_motorcycle_frontend.controllers.main.MotorCycleWebsiteSale.

    """

    @http.route()
    def shop(self, page=0, category=None, search='', min_price=0.0, max_price=0.0, ppg=False, **post):
        res = super().shop(page, category, search, min_price, max_price, ppg, **post)

        if hasattr(res, 'qcontext') and 'products' in res.qcontext:
            public_products = res.qcontext['products']

            # Buscamos las variantes por cada template
            variants = request.env['product.product'].sudo().search([
                ('product_tmpl_id', 'in', public_products.ids)
            ])
            variant_data = variants.read(['product_tmpl_id', 'qty_available'])

            # Sumamos disponibilidad por template
            stock_map = {}
            for line in variant_data:
                tmpl_id = line['product_tmpl_id'][0] if line['product_tmpl_id'] else None
                if tmpl_id:
                    stock_map[tmpl_id] = stock_map.get(tmpl_id, 0) + line['qty_available']

            # Creamos un mapa {product.id: True/False}
            has_stock_map = {pid: (qty > 0) for pid, qty in stock_map.items()}

            # Lo inyectamos al contexto
            res.qcontext['has_stock_map'] = has_stock_map

        return res



    """ este metodo sirve para pagina de producto INDIVIDUAL """

    # def _prepare_product_values(self, product, category, search, **kwargs):

    #     values = super(BiagioliWebsiteSale, self)._prepare_product_values(
    #         product, category, search, **kwargs)


    #     return values
    
