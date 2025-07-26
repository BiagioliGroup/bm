# # -*- coding: utf-8 -*-
# # Sergio Biagioli Code

# from odoo.addons.sh_motorcycle_frontend.controllers.sh_motorcycle_frontend import MotorCycleWebsiteSale
# from odoo.http import request
# from odoo import http
# import logging


# _logger = logging.getLogger(__name__)


# class BiagioliWebsiteSale(MotorCycleWebsiteSale):

#     """ Aqui es donde vamos a inyectar el stock de los productos en la pagina de shop y cualquier otro dato que queramos

#         Gran Dato: DEPENDEMOS DE sh_motorcycle_frontend.controllers.main.MotorCycleWebsiteSale.

#     """

#     @http.route([
#         '/shop',
#         '/shop/page/<int:page>'
#     ], type='http', auth="public", website=True)
#     def shop(self, page=0, category=None, search='', min_price=0.0,
#              max_price=0.0, ppg=False, **post):
#         res = super(BiagioliWebsiteSale, self).shop(
#             page, category, search, min_price, max_price, ppg, **post
#         )

#         # SIEMPRE inicializamos el mapa, aunque no haya productos
#         has_stock_map = {}

#         if hasattr(res, 'qcontext'):
#             products = res.qcontext.get('products') or request.env['product.template']
#             if products:
#                 # calculamos el stock agregado por template
#                 variants = request.env['product.product'].sudo().search([
#                     ('product_tmpl_id', 'in', products.ids)
#                 ]).read(['product_tmpl_id', 'qty_available'])
#                 stock_map = {}
#                 for line in variants:
#                     tid = line['product_tmpl_id'][0]
#                     stock_map[tid] = stock_map.get(tid, 0) + line['qty_available']
#                 has_stock_map = {tid: (qty > 0) for tid, qty in stock_map.items()}

#             # inyectamos el dict (aunque esté vacío) para evitar KeyError
#             res.qcontext['has_stock_map'] = has_stock_map

#         return res


#     """ este metodo sirve para pagina de producto INDIVIDUAL """

#     # def _prepare_product_values(self, product, category, search, **kwargs):

#     #     values = super(BiagioliWebsiteSale, self)._prepare_product_values(
#     #         product, category, search, **kwargs)


#     #     return values
    
