# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api, _
from odoo.fields import Command


class ServiceTemplateWizard(models.TransientModel):
    _name = 'service.template.wizard'
    _description = 'Wizard para Seleccionar Plantilla de Servicio'

    sale_order_id = fields.Many2one(
        'sale.order',
        string='Orden de Venta',
        required=True,
        readonly=True
    )
    
    service_template_id = fields.Many2one(
        'motorcycle.service',
        string='Plantilla de Servicio',
        required=True,
        domain="[('service_line_ids', '!=', False)]"
    )
    
    add_section_header = fields.Boolean(
        string='Agregar Encabezado de Sección',
        default=True,
        help="Agrega una sección con el nombre del servicio como encabezado"
    )
    
    section_name = fields.Char(
        string='Nombre de Sección',
        help="Nombre personalizado para la sección (por defecto usa el nombre del servicio)"
    )

    @api.onchange('service_template_id')
    def _onchange_service_template_id(self):
        """Establecer nombre de sección por defecto"""
        if self.service_template_id and not self.section_name:
            self.section_name = self.service_template_id.name

    def action_apply_template(self):
        """Aplicar la plantilla seleccionada a la orden de venta"""
        self.ensure_one()
        
        if not self.service_template_id:
            return
        
        sale_order = self.sale_order_id
        template = self.service_template_id
        lines_to_add = []
        
        # Obtener la secuencia actual más alta
        current_sequences = [line.sequence for line in sale_order.order_line if line.sequence]
        next_sequence = max(current_sequences) + 10 if current_sequences else 10
        
        # Agregar encabezado de sección si está marcado
        if self.add_section_header:
            lines_to_add.append(Command.create({
                'display_type': 'line_section',
                'name': self.section_name or template.name,
                'sequence': next_sequence,
            }))
            next_sequence += 1
        
        # Procesar líneas del servicio
        for service_line in template.service_line_ids:
            if service_line.display_type == 'line_section':
                lines_to_add.append(Command.create({
                    'display_type': 'line_section',
                    'name': service_line.name,
                    'sequence': next_sequence,
                }))
                
            elif service_line.display_type == 'line_note':
                lines_to_add.append(Command.create({
                    'display_type': 'line_note',
                    'name': service_line.name,
                    'sequence': next_sequence,
                }))
                
            elif service_line.display_type == 'line' and service_line.product_id:
                # Preparar valores de línea de producto
                line_vals = {
                    'product_id': service_line.product_id.id,
                    'name': service_line.name,
                    'product_uom_qty': service_line.quantity,
                    'price_unit': service_line.price_unit,
                    'sequence': next_sequence,
                }
                
                # Aplicar impuestos según posición fiscal
                if service_line.product_id and sale_order.fiscal_position_id:
                    product_taxes = service_line.product_id.taxes_id
                    taxes = sale_order.fiscal_position_id.map_tax(product_taxes)
                    line_vals['tax_id'] = [Command.set(taxes.ids)]
                elif service_line.product_id:
                    line_vals['tax_id'] = [Command.set(service_line.product_id.taxes_id.ids)]
                
                lines_to_add.append(Command.create(line_vals))
            
            next_sequence += 1
        
        # Agregar líneas a la orden
        if lines_to_add:
            sale_order.write({'order_line': lines_to_add})
        
        # Mostrar mensaje de éxito
        message = _("Se agregaron %d líneas desde la plantilla '%s'") % (
            len(lines_to_add), template.name
        )
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Plantilla Aplicada'),
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }