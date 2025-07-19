from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    sale_order_ids = fields.One2many(
        'sale.order', 
        'sale_invoice_id', 
        string='Pedidos de Venta asociados'
    )
