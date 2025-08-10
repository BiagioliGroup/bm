# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Campo para plantilla de servicios de motocicleta
    motorcycle_service_template_id = fields.Many2one(
        'motorcycle.service',
        string='Plantilla de Servicios',
        help='Seleccionar una plantilla de servicio para agregar líneas automáticamente'
    )

    # Agregar campos personalizados para motocicletas
    motorcycle_ids = fields.Many2many(
        'motorcycle.motorcycle',
        'sale_order_motorcycle_rel',
        'order_id', 'motorcycle_id',
        string='Motocicletas Relacionadas'
    )

    def action_clear_order_lines(self):
        """Método para limpiar todas las líneas de pedido"""
        self.ensure_one()
        
        # Verificar que el pedido esté en estado borrador o enviado
        if self.state not in ['draft', 'sent']:
            raise UserError(_('Solo puedes borrar líneas en pedidos en borrador o enviados.'))
        
        # Eliminar todas las líneas excepto las de pago inicial y secciones importantes
        lines_to_remove = self.order_line.filtered(
            lambda line: not line.is_downpayment and line.display_type != 'line_section'
        )
        
        if lines_to_remove:
            lines_to_remove.unlink()
            self.message_post(
                body=_('Se eliminaron %d líneas del pedido de venta.') % len(lines_to_remove)
            )
        else:
            raise UserError(_('No hay líneas para eliminar.'))
        
        return True

    @api.onchange('motorcycle_service_template_id')
    def _onchange_motorcycle_service_template_id(self):
        """Agregar líneas automáticamente desde la plantilla seleccionada"""
        if self.motorcycle_service_template_id:
            # Limpiar líneas existentes primero (opcional)
            # self.order_line = [(5, 0, 0)]  # Descomentar si quieres limpiar automáticamente
            
            lines_to_add = []
            template = self.motorcycle_service_template_id
            
            # Agregar líneas desde la plantilla de servicio
            for service_line in template.service_line_ids:
                if service_line.product_id:
                    line_vals = {
                        'product_id': service_line.product_id.id,
                        'name': service_line.name or service_line.product_id.name,
                        'product_uom_qty': service_line.quantity,
                        'price_unit': service_line.price_unit,
                        'product_uom': service_line.product_id.uom_id.id,
                    }
                    lines_to_add.append((0, 0, line_vals))
            
            if lines_to_add:
                self.order_line = lines_to_add

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # Agregar campos personalizados para líneas de venta
    motorcycle_id = fields.Many2one(
        'motorcycle.motorcycle',
        string='Motocicleta'
    )
    
    # Relación con servicios de motocicleta si es necesario
    service_line_ids = fields.One2many(
        'motorcycle.service.line',
        'sale_line_id',
        string='Líneas de Servicio'
    )

    @api.onchange('motorcycle_id')
    def _onchange_motorcycle_id(self):
        """Filtrar productos compatibles con la motocicleta seleccionada"""
        if self.motorcycle_id:
            compatible_products = self.env['product.product'].search([
                ('motorcycle_ids', 'in', self.motorcycle_id.id)
            ])
            return {'domain': {'product_id': [('id', 'in', compatible_products.ids)]}}
        return {'domain': {'product_id': []}}