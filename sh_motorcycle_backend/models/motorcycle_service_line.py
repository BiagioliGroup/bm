# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api

class MotorcycleServiceLine(models.Model):
    _name = 'motorcycle.service.line'
    _description = 'Línea del Servicio de Motocicleta'
    _order = 'sequence, id'

    service_id = fields.Many2one(
        'motorcycle.service', string='Servicio de Motocicleta', required=True, ondelete='cascade'
    )
    sequence = fields.Integer(string='Secuencia', default=10)
    display_type = fields.Selection(
        [('line', 'Producto'), ('section', 'Sección'), ('note', 'Nota')],
        string='Tipo de línea', default='line', required=True
    )
    product_id = fields.Many2one('product.product', string='Producto')
    name = fields.Text(string='Descripción')
    quantity = fields.Float(string='Cantidad', default=1.0)
    price_unit = fields.Float(string='Precio unitario')
    subtotal = fields.Monetary(
        string='Subtotal', compute='_compute_subtotal', store=True, currency_field='currency_id'
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        related='service_id.currency_id',
        readonly=True,
        store=True
    )

    @api.depends('display_type', 'quantity', 'price_unit')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.price_unit if line.display_type == 'line' else 0.0

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.name
            self.price_unit = self.product_id.list_price


class MotorcycleServiceStep(models.Model):
    _name = 'motorcycle.service.step'
    _description = 'Paso operativo del servicio técnico'
    _order = 'sequence, id'

    service_id = fields.Many2one(
        'motorcycle.service', string='Servicio de Motocicleta', required=True, ondelete='cascade'
    )
    sequence = fields.Integer(string='Secuencia', default=10)
    name = fields.Char(string='Descripción del paso', required=True)
    step_type = fields.Selection([
        ('action', 'Acción'),
        ('decision', 'Punto de Decisión'),
        ('start', 'Inicio'),
        ('end', 'Fin')
    ], string='Tipo de Paso', default='action', required=True)
    is_done = fields.Boolean(string='Completado')
    note = fields.Text(string='Nota o instrucción especial')
    pdf_file = fields.Binary(string='Archivo PDF', attachment=True)
    pdf_filename = fields.Char(string='Nombre del archivo')
    
    # Campos para puntos de decisión
    decision_question = fields.Text(string='Pregunta de Decisión')
    next_step_yes_id = fields.Many2one(
        'motorcycle.service.step', 
        string='Siguiente Paso (SÍ)',
        help="Paso a seguir si la respuesta es SÍ"
    )
    next_step_no_id = fields.Many2one(
        'motorcycle.service.step', 
        string='Siguiente Paso (NO)',
        help="Paso a seguir si la respuesta es NO"
    )
    
    # Campo para conexiones de pasos normales
    next_step_id = fields.Many2one(
        'motorcycle.service.step',
        string='Siguiente Paso',
        help="Siguiente paso en el flujo normal"
    )
    
    # Campos computados para el display
    step_icon = fields.Char(string='Ícono', compute='_compute_step_icon')
    step_color = fields.Char(string='Color', compute='_compute_step_color')
    
    @api.depends('step_type')
    def _compute_step_icon(self):
        icon_map = {
            'action': 'fa-cog',
            'decision': 'fa-question-circle',
            'start': 'fa-play',
            'end': 'fa-stop'
        }
        for step in self:
            step.step_icon = icon_map.get(step.step_type, 'fa-cog')
    
    @api.depends('step_type', 'is_done')
    def _compute_step_color(self):
        for step in self:
            if step.is_done:
                step.step_color = '#28a745'  # Verde para completado
            elif step.step_type == 'decision':
                step.step_color = '#ffc107'  # Amarillo para decisiones
            elif step.step_type == 'start':
                step.step_color = '#007bff'  # Azul para inicio
            elif step.step_type == 'end':
                step.step_color = '#dc3545'  # Rojo para fin
            else:
                step.step_color = '#6c757d'  # Gris para acciones normales