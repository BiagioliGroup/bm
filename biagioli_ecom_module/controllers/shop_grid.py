# -*- coding: utf-8 -*-
# Sergio Biagioli Code

from odoo.addons.sh_motorcycle_frontend.controllers.sh_motorcycle_frontend import MotorCycleWebsiteSale
from odoo.http import request
from odoo import http

_logger = logging.getLogger(__name__)


class BiagioliWebsiteSale(WebsiteSale):

    """ Aqui es donde vamos a inyectar el stock de los productos en la pagina de shop y cualquier otro dato que queramos

        Gran Dato: DEPENDEMOS DE sh_motorcycle_frontend.controllers.main.MotorCycleWebsiteSale.

    """

    @http.route()
    def shop(self, page=0, category=None, search='', min_price=0.0, max_price=0.0, ppg=False, **post):
        res = super().shop(page, category, search, min_price, max_price, ppg, **post)

        if hasattr(res, 'qcontext') and 'products' in res.qcontext:
            public_products = res.qcontext['products']

            # Calculamos el stock básico sin acceder a qty_available directamente
            product_stocks = request.env['product.product'].sudo().read_group(
                [('product_tmpl_id', 'in', public_products.ids)],
                ['product_tmpl_id', 'qty_available'],
                ['product_tmpl_id']
            )

            # Mapeamos por template ID
            stock_map = {
                group['product_tmpl_id'][0]: group['qty_available']
                for group in product_stocks
            }

            # Inyectamos un nuevo atributo a cada product.template
            for product in public_products:
                product.has_stock = stock_map.get(product.id, 0) > 0

        return res



    """ este metodo sirve para pagina de producto INDIVIDUAL """

    # def _prepare_product_values(self, product, category, search, **kwargs):

    #     values = super(BiagioliWebsiteSale, self)._prepare_product_values(
    #         product, category, search, **kwargs)


    #     return values
    
