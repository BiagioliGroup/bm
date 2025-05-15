from odoo import models

class ProductProduct(models.Model):
    _inherit = 'product.product'

    def action_apply_ribbon_by_supplier(self):
        for producto in self:
            # Obtener primer proveedor (si existe)
            supplierinfo = producto.seller_ids[:1]
            if not supplierinfo or not supplierinfo.partner_id:
                continue

            proveedor = supplierinfo.partner_id

            # Buscar el stock total del producto en todas las ubicaciones
            stock_total = sum(producto.env['stock.quant'].search([
                ('product_id', '=', producto.id)
            ]).mapped('quantity'))

            # Si no hay stock, aplicar la lógica
            if stock_total == 0:
                if proveedor.country_id and proveedor.country_id.code == "AR":
                    producto.website_ribbon_id = 6  # 24 hs de demora
                else:
                    producto.website_ribbon_id = 5  # para Importar

