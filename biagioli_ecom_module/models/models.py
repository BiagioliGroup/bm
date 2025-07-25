from odoo import models

class ProductProduct(models.Model):
    _inherit = 'product.product'

    def action_apply_ribbon_by_supplier(self):
        for producto in self:
            supplierinfo = producto.seller_ids[:1]
            if not supplierinfo or not supplierinfo.partner_id:
                continue

            proveedor = supplierinfo.partner_id

            # Calcular stock total desde stock.quant
            stock_total = sum(producto.env['stock.quant'].search([
                ('product_id', '=', producto.id)
            ]).mapped('quantity'))

            # Aplicar la cinta si no hay stock
            if stock_total == 0:
                if proveedor.country_id and proveedor.country_id.code == "AR":
                    producto.product_tmpl_id.website_ribbon_id = 6
                else:
                    producto.product_tmpl_id.website_ribbon_id = 5


