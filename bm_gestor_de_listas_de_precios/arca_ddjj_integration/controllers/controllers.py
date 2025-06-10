# -*- coding: utf-8 -*-
# from odoo import http


# class ArcaDdjjIntegration(http.Controller):
#     @http.route('/arca_ddjj_integration/arca_ddjj_integration', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/arca_ddjj_integration/arca_ddjj_integration/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('arca_ddjj_integration.listing', {
#             'root': '/arca_ddjj_integration/arca_ddjj_integration',
#             'objects': http.request.env['arca_ddjj_integration.arca_ddjj_integration'].search([]),
#         })

#     @http.route('/arca_ddjj_integration/arca_ddjj_integration/objects/<model("arca_ddjj_integration.arca_ddjj_integration"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('arca_ddjj_integration.object', {
#             'object': obj
#         })

