# -*- coding: utf-8 -*-
# from odoo import http


# class BiagioliMercadopagoPatch(http.Controller):
#     @http.route('/biagioli_mercadopago_patch/biagioli_mercadopago_patch', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/biagioli_mercadopago_patch/biagioli_mercadopago_patch/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('biagioli_mercadopago_patch.listing', {
#             'root': '/biagioli_mercadopago_patch/biagioli_mercadopago_patch',
#             'objects': http.request.env['biagioli_mercadopago_patch.biagioli_mercadopago_patch'].search([]),
#         })

#     @http.route('/biagioli_mercadopago_patch/biagioli_mercadopago_patch/objects/<model("biagioli_mercadopago_patch.biagioli_mercadopago_patch"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('biagioli_mercadopago_patch.object', {
#             'object': obj
#         })

