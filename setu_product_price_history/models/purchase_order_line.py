from odoo import api, models, fields, _


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    previous_unit_price = fields.Float(string="Previous Unit Price", store="True", copy=False)

    serial_number = fields.Integer(string="Sr.no", compute="create_serial_number_for_line")

    @api.depends('sequence')
    def create_serial_number_for_line(self):
        """
            Author: jatin.babariya@setuconsulting.com
            Date: 30 Dec 2024 | Task no: [1394] Product Price History
            Purpose: Create Serial Number.
        """
        process_orders = []
        for line in self:
            purchase = line.order_id
            if purchase.id in process_orders:
                continue
            serial_number = 1
            for line in purchase.order_line.sorted(key='sequence'):
                line.write({'serial_number': serial_number})
                if not line.display_type:
                    serial_number += 1
            process_orders.append(purchase.id)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """
            Author: jatin.babariya@setuconsulting.com
            Date: 30 Dec 2024 | Task no: [1394] Product Price History
            Purpose: Set previous_unit_price in current record.
        """
        for record in self:
            purchase_order_line = self.env['purchase.order.line'].search(
                [('order_id.state', 'not in', ['cancel']), ('order_id.partner_id', '=', record.order_id.partner_id.id),
                 ('product_id', '=', record.product_id.id), ('order_id', '!=', record.order_id._origin.id)],
                order='id desc', limit=1)
            record.previous_unit_price = purchase_order_line.price_unit

    def show_product_purchase_lines(self):
        """
            Author: jatin.babariya@setuconsulting.com
            Date: 30 Dec 2024 | Task no: [1394] Product Price History
            Purpose: Open Purchase Order Lines Tree View(product price history).
        """
        lines = self.search([('order_id', '!=', self.order_id.id), ('product_id', '=', self.product_id.id)],
                            order='id desc')
        lines = lines.filtered(lambda line: line.order_id.state in ['purchase', 'done'])
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'list',
            'res_model': 'purchase.order.line',
            'name': '%s' % (self.product_id.display_name),
            'views': [
                (self.env.ref('setu_product_price_history.setu_purchase_order_line_tree').id, 'list'),
            ],
            'domain': [('id', 'in', lines._ids)],
            'target': 'new',
        }
