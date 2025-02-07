from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    previous_unit_price = fields.Float(string="Previous Unit Price", store="True", copy=False)
    date_order = fields.Datetime(related='order_id.date_order')
    product_sale_id_reference = fields.Integer(related='product_id.id', store=True, string='')
    product_purchase_id_reference = fields.Integer(related='product_id.id', store=True, string='')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """
            Author: jatin.babariya@setuconsulting.com
            Date: 30 Dec 2024 | Task no: [1394] Product Price History
            Purpose: Set previous_unit_price in current record.
        """
        for record in self:
            sale_order_line = self.env['sale.order.line'].search(
                [('order_id.state', 'not in', ['cancel']), ('order_id.partner_id', '=', record.order_id.partner_id.id),
                 ('product_id', '=', record.product_id.id), ('order_id', '!=', record.order_id._origin.id)],
                order='id desc', limit=1)
            record.previous_unit_price = sale_order_line.price_unit

    def show_product_sale_lines(self, args):
        """
            Author: jatin.babariya@setuconsulting.com
            Date: 30 Dec 2024 | Task no: [1394] Product Price History
            Purpose: Open Sale Order Lines Tree View(product price history).
        """
        product = self.env['product.product'].search([('id', '=', int(args))])
        lines = self.search([('order_id', '!=', self.order_id.id), ('state', '!=', 'cancel'),
                             ('product_id', '=', product.id)], order='id desc')
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'list',
            'res_model': 'sale.order.line',
            'name': '%s' % (product.display_name),
            'views': [
                (self.env.ref('setu_product_price_history.setu_view_order_line_tree').id, 'list'),
            ],
            'domain': [('id', 'in', lines._ids)],
            'target': 'new',
        }

    def show_product_purchase_lines(self, args):
        """
            Author: jatin.babariya@setuconsulting.com
            Date: 30 Dec 2024 | Task no: [1394] Product Price History
            Purpose: Open Purchase Order Lines Tree View(product price history).
        """
        product = self.env['product.product'].search([('id', '=', int(args))])
        lines = self.env['purchase.order.line'].search(
            [('product_id', '=', product.id), ('state', 'in', ['purchase', 'done'])], order='id desc')
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'list',
            'res_model': 'purchase.order.line',
            'name': '%s' % (product.display_name),
            'views': [
                (self.env.ref('setu_product_price_history.setu_purchase_order_line_tree').id, 'list'),
            ],
            'domain': [('id', 'in', lines._ids)],
            'target': 'new',
        }
