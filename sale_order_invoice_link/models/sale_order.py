from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sale_invoice_id = fields.Many2one(
        'account.move', 
        string='Factura asociada',
        compute='_compute_sale_invoice_id',
        store=True,
    )

 

    @api.depends('invoice_ids', 'invoice_ids.state')
    def _compute_sale_invoice_id(self):
        for order in self:
            # Tomamos la primera factura validada (state = 'posted')
            invoices = order.invoice_ids.filtered(lambda inv: inv.state == 'posted')
            order.sale_invoice_id = invoices and invoices[0].id or False
