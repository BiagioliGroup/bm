from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    sale_order_ids = fields.One2many(
        'sale.order', 
        'sale_invoice_id', 
        string='Pedidos de Venta asociados'
    )

    repair_order_ids = fields.Many2many(
        'repair.order',              # Modelo de reparación
        compute='_compute_repair_orders',
        string='Órdenes de Reparación',
        store=True,
    )

    @api.depends('sale_order_ids')    # recalcula cuando cambie la relación a pedidos
    def _compute_repair_orders(self):
        Repair = self.env['repair.order']
        for move in self:
            # obtén todos los sale.order vinculados a esta factura
            sale_ids = move.sale_order_ids.ids
            # busca las repair.order que apunten a esos pedidos
            recs = Repair.search([('sale_order_id', 'in', sale_ids)])
            move.repair_order_ids = recs.ids