# -*- coding: utf-8 -*-
# Métodos adicionales para el modelo SaleOrder

from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_open_service_template_wizard(self):
        """Abrir wizard para seleccionar plantilla de servicio"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Agregar Plantilla de Servicio'),
            'res_model': 'service.template.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_order_id': self.id,
            },
        }

    def action_quick_add_service_template(self):
        """Método rápido para agregar plantilla sin wizard"""
        self.ensure_one()
        
        # Buscar plantillas disponibles
        templates = self.env['motorcycle.service'].search([
            ('service_line_ids', '!=', False)
        ])
        
        if not templates:
            return {
                'warning': {
                    'title': _('Sin Plantillas'),
                    'message': _('No hay plantillas de servicios disponibles.')
                }
            }
        
        if len(templates) == 1:
            # Si solo hay una plantilla, aplicarla directamente
            self.motorcycle_service_template_id = templates.id
            self._onchange_motorcycle_service_template_id()
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Plantilla Aplicada'),
                    'message': _('Se aplicó la plantilla "%s"') % templates.name,
                    'type': 'success',
                }
            }
        else:
            # Si hay múltiples plantillas, abrir selector
            return {
                'type': 'ir.actions.act_window',
                'name': _('Seleccionar Plantilla'),
                'res_model': 'motorcycle.service',
                'view_mode': 'list',
                'target': 'new',
                'domain': [('service_line_ids', '!=', False)],
                'context': {
                    'search_default_group_by_motorcycle': 1,
                }
            }

    def _get_available_service_templates(self):
        """Obtener plantillas de servicios disponibles"""
        return self.env['motorcycle.service'].search([
            ('service_line_ids', '!=', False)
        ])

    def _add_service_template_lines(self, template, add_section=True, section_name=None):
        """Método auxiliar para agregar líneas de plantilla de servicio"""
        self.ensure_one()
        
        if not template or not template.service_line_ids:
            return False
        
        lines_to_add = []
        
        # Obtener secuencia siguiente
        current_sequences = [line.sequence for line in self.order_line if line.sequence]
        next_sequence = max(current_sequences) + 10 if current_sequences else 10
        
        # Agregar sección encabezado si se solicita
        if add_section:
            section_title = section_name or template.name
            lines_to_add.append((0, 0, {
                'display_type': 'line_section',
                'name': section_title,
                'sequence': next_sequence,
            }))
            next_sequence += 1
        
        # Agregar líneas del servicio
        for service_line in template.service_line_ids:
            line_vals = {
                'sequence': next_sequence,
            }
            
            if service_line.display_type in ['line_section', 'line_note']:
                line_vals.update({
                    'display_type': service_line.display_type,
                    'name': service_line.name,
                })
            else:
                # Línea de producto
                line_vals.update({
                    'product_id': service_line.product_id.id,
                    'name': service_line.name,
                    'product_uom_qty': service_line.quantity,
                    'price_unit': service_line.price_unit,
                })
                
                # Aplicar impuestos
                if service_line.product_id:
                    taxes = service_line.product_id.taxes_id
                    if self.fiscal_position_id:
                        taxes = self.fiscal_position_id.map_tax(taxes)
                    if taxes:
                        line_vals['tax_id'] = [(6, 0, taxes.ids)]
            
            lines_to_add.append((0, 0, line_vals))
            next_sequence += 1
        
        # Escribir las líneas
        if lines_to_add:
            self.write({'order_line': lines_to_add})
            return len(lines_to_add)
        
        return 0

    @api.model
    def create(self, vals):
        """Override create para manejar plantilla de servicio en creación"""
        order = super().create(vals)
        
        # Si se especifica una plantilla de servicio al crear, aplicarla
        if vals.get('motorcycle_service_template_id'):
            template = self.env['motorcycle.service'].browse(vals['motorcycle_service_template_id'])
            if template.exists():
                order._add_service_template_lines(template)
                # Limpiar el campo
                order.motorcycle_service_template_id = False
        
        return order