# -*- coding: utf-8 -*-
# from odoo import http


# class Viumi-payment(http.Controller):
#     @http.route('/viumi-payment/viumi-payment', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/viumi-payment/viumi-payment/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('viumi-payment.listing', {
#             'root': '/viumi-payment/viumi-payment',
#             'objects': http.request.env['viumi-payment.viumi-payment'].search([]),
#         })

#     @http.route('/viumi-payment/viumi-payment/objects/<model("viumi-payment.viumi-payment"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('viumi-payment.object', {
#             'object': obj
#         })

