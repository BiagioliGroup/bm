# -*- coding: utf-8 -*-
# from odoo import http


# class BiagioliEcomModule(http.Controller):
#     @http.route('/biagioli_ecom_module/biagioli_ecom_module', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/biagioli_ecom_module/biagioli_ecom_module/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('biagioli_ecom_module.listing', {
#             'root': '/biagioli_ecom_module/biagioli_ecom_module',
#             'objects': http.request.env['biagioli_ecom_module.biagioli_ecom_module'].search([]),
#         })

#     @http.route('/biagioli_ecom_module/biagioli_ecom_module/objects/<model("biagioli_ecom_module.biagioli_ecom_module"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('biagioli_ecom_module.object', {
#             'object': obj
#         })

