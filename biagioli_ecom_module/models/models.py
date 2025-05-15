from odoo import models

class ProductProduct(models.Model):
    _inherit = 'product.product'

    def action_apply_ribbon_by_supplier(self):
        for producto in self:
            supplierinfo = producto.seller_ids[:1]
            if supplierinfo and supplierinfo.name and producto.inventory_quantity_auto_apply == 0:
                proveedor = supplierinfo.name
                if proveedor.country_id and proveedor.country_id.name == "Argentina":
                    producto.website_ribbon_id = 6  # 24 hs de demora
                else:
                    producto.website_ribbon_id = 5  # para Importar
