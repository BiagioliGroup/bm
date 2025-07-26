# biagioli_ecom_module/controllers/stock_map.py
from odoo import http
from odoo.http import request

class BiagioliStockMap(http.Controller):

    @http.route('/biagioli/stock_map', type='json', auth='public', website=True)
    def stock_map(self, product_ids):
        records = request.env['product.template'].sudo().browse(product_ids)
        data = records.read(['id', 'qty_available'])
        return {r['id']: r['qty_available'] for r in data}
    