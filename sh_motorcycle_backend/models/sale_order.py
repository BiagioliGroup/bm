# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api, _
from odoo.fields import Command


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    motorcycle_service_template_id = fields.Many2one(
        'motorcycle.service',
        string='Plantilla de Servicios',
        help="Selecciona una plantilla de servicio para agregar automáticamente todas sus líneas a esta orden de venta."
    )

    @api.onchange('motorcycle_service_template_id')
    def _onchange_motorcycle_service_template_id(self):
        """Agregar líneas de la plantilla de servicio seleccionada"""
        if not self.motorcycle_service_template_id:
            return

        template = self.motorcycle_service_template_id
        lines_to_add = []

        # Obtener la secuencia actual más alta para agregar al final
        current_sequences = [line.sequence for line in self.order_line if line.sequence]
        next_sequence = max(current_sequences) + 10 if current_sequences else 10

        # Procesar las líneas del servicio
        for service_line in template.service_line_ids:
            if service_line.display_type == 'line_section':
                # Agregar sección
                lines_to_add.append(Command.create({
                    'display_type': 'line_section',
                    'name': service_line.name,
                    'sequence': next_sequence,
                }))
                next_sequence += 1
                
            elif service_line.display_type == 'line_note':
                # Agregar nota
                lines_to_add.append(Command.create({
                    'display_type': 'line_note',
                    'name': service_line.name,
                    'sequence': next_sequence,
                }))
                next_sequence += 1
                
            elif service_line.display_type == 'line' and service_line.product_id:
                # Agregar línea de producto
                line_vals = {
                    'product_id': service_line.product_id.id,
                    'name': service_line.name,
                    'product_uom_qty': service_line.quantity,
                    'price_unit': service_line.price_unit,
                    'sequence': next_sequence,
                }
                
                # Si el producto tiene impuestos, los asignamos
                if service_line.product_id:
                    # Obtener impuestos según la posición fiscal
                    product_taxes = service_line.product_id.taxes_id
                    if self.fiscal_position_id:
                        product_taxes = self.fiscal_position_id.map_tax(product_taxes)
                    line_vals['tax_id'] = [Command.set(product_taxes.ids)]
                
                lines_to_add.append(Command.create(line_vals))
                next_sequence += 1

        # Agregar todas las líneas a la orden
        if lines_to_add:
            self.order_line = lines_to_add
            
            # Mensaje informativo
            message = _("Se agregaron %d líneas desde la plantilla de servicio '%s'") % (
                len(lines_to_add), template.name
            )
            
            # En caso de estar en el contexto web, mostrar notificación
            if self.env.context.get('active_model') == 'sale.order':
                return {
                    'warning': {
                        'title': _('Plantilla Aplicada'),
                        'message': message
                    }
                }

        # Limpiar el campo de plantilla para evitar aplicarla nuevamente
        self.motorcycle_service_template_id = False

    def action_apply_service_template(self):
        """Método alternativo para aplicar plantilla desde botón"""
        self.ensure_one()
        if not self.motorcycle_service_template_id:
            return {
                'warning': {
                    'title': _('Sin Plantilla'),
                    'message': _('Por favor selecciona una plantilla de servicio primero.')
                }
            }
        
        # Aplicar la plantilla
        self._onchange_motorcycle_service_template_id()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Plantilla Aplicada'),
                'message': _('Las líneas de servicio se agregaron correctamente.'),
                'type': 'success',
                'sticky': False,
            }
        }

    @api.model
    def _get_service_template_domain(self):
        """Dominio para filtrar plantillas de servicio disponibles"""
        return [
            ('service_line_ids', '!=', False),  # Solo servicios con líneas
        ]


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.model
    def _prepare_service_template_line(self, service_line, sequence):
        """Preparar valores para línea desde plantilla de servicio"""
        if service_line.display_type in ['line_section', 'line_note']:
            return {
                'display_type': service_line.display_type,
                'name': service_line.name,
                'sequence': sequence,
            }
        
        # Línea de producto
        vals = {
            'product_id': service_line.product_id.id,
            'name': service_line.name,
            'product_uom_qty': service_line.quantity,
            'price_unit': service_line.price_unit,
            'sequence': sequence,
        }
        
        return vals