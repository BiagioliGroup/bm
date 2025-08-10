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

    @api.depends('product_id', 'display_type')
    def _compute_name(self):
        for line in self:
            if not line.name:
                if line.display_type == 'section':
                    line.name = 'Nueva Sección'
                elif line.display_type == 'note':
                    line.name = 'Nueva Nota'
                elif line.product_id:
                    line.name = line.product_id.name
                else:
                    line.name = 'Línea de Servicio'

    @api.depends('display_type', 'quantity', 'price_unit')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.price_unit if line.display_type == 'line' else 0.0

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.name
            self.price_unit = self.product_id.list_price

    def add_line_product(self):
        self.ensure_one()
        self.env['motorcycle.service.line'].create({
            'service_id': self.id,
            'display_type': 'line',
            'name': 'Nueva línea de producto',
            'quantity': 1,
            'price_unit': 0,
        })

    def add_line_section(self):
        self.ensure_one()
        self.env['motorcycle.service.line'].create({
            'service_id': self.id,
            'display_type': 'section',
            'name': 'Nueva sección',
        })

    def add_line_note(self):
        self.ensure_one()
        self.env['motorcycle.service.line'].create({
            'service_id': self.id,
            'display_type': 'note',
            'name': 'Nueva nota',
        })


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
        ('start', 'Inicio'),
        ('action', 'Acción'),
        ('decision', 'Punto de Decisión'),
        ('end', 'Fin')
    ], string='Tipo de Paso', default='action', required=True)
    is_done = fields.Boolean(string='Completado')
    note = fields.Text(string='Nota o instrucción especial')
    pdf_file = fields.Binary(string='Archivo PDF', attachment=True)
    pdf_filename = fields.Char(string='Nombre del archivo')
    
    # Campos para posicionamiento en el diagrama
    position_x = fields.Float(string='Posición X', default=100)
    position_y = fields.Float(string='Posición Y', default=100)
    
    # Campos para puntos de decisión
    decision_question = fields.Text(string='Pregunta de Decisión')
    next_step_yes_id = fields.Many2one(
        'motorcycle.service.step', 
        string='Siguiente Paso (SÍ)',
        help="Paso a seguir si la respuesta es SÍ",
        domain="[('service_id', '=', service_id), ('id', '!=', id)]"
    )
    next_step_no_id = fields.Many2one(
        'motorcycle.service.step', 
        string='Siguiente Paso (NO)',
        help="Paso a seguir si la respuesta es NO",
        domain="[('service_id', '=', service_id), ('id', '!=', id)]"
    )
    
    # Campo para conexiones de pasos normales
    next_step_id = fields.Many2one(
        'motorcycle.service.step',
        string='Siguiente Paso',
        help="Siguiente paso en el flujo normal",
        domain="[('service_id', '=', service_id), ('id', '!=', id)]"
    )
    
    # Campos computados para el display
    step_icon = fields.Char(string='Ícono', compute='_compute_step_display', store=True)
    step_color = fields.Char(string='Color', compute='_compute_step_display', store=True)
    step_class = fields.Char(string='Clase CSS', compute='_compute_step_display', store=True)
    
    @api.depends('step_type', 'is_done')
    def _compute_step_display(self):
        for step in self:
            if step.step_type == 'start':
                step.step_icon = 'fa-play-circle'
                step.step_color = '#007bff'
                step.step_class = 'workflow-start'
            elif step.step_type == 'action':
                step.step_icon = 'fa-cog'
                step.step_color = '#28a745' if step.is_done else '#6c757d'
                step.step_class = 'workflow-action'
            elif step.step_type == 'decision':
                step.step_icon = 'fa-question-circle'
                step.step_color = '#ffc107'
                step.step_class = 'workflow-decision'
            elif step.step_type == 'end':
                step.step_icon = 'fa-stop-circle'
                step.step_color = '#dc3545'
                step.step_class = 'workflow-end'
            else:
                step.step_icon = 'fa-circle'
                step.step_color = '#6c757d'
                step.step_class = 'workflow-default'

    def get_connections_data(self):
        """Obtiene datos de conexiones para el frontend"""
        connections = []
        
        # Conexión normal
        if self.next_step_id:
            connections.append({
                'from': self.id,
                'to': self.next_step_id.id,
                'type': 'normal',
                'label': ''
            })
        
        # Conexiones de decisión
        if self.step_type == 'decision':
            if self.next_step_yes_id:
                connections.append({
                    'from': self.id,
                    'to': self.next_step_yes_id.id,
                    'type': 'yes',
                    'label': 'SÍ'
                })
            if self.next_step_no_id:
                connections.append({
                    'from': self.id,
                    'to': self.next_step_no_id.id,
                    'type': 'no',
                    'label': 'NO'
                })
        
        return connections

    @api.model
    def create_workflow_template(self, service_id):
        """Crear plantilla básica de workflow"""
        steps_data = [
            {
                'service_id': service_id,
                'name': 'Inicio del Servicio',
                'step_type': 'start',
                'sequence': 10,
                'position_x': 100,
                'position_y': 100,
                'note': 'Punto de inicio del proceso'
            },
            {
                'service_id': service_id,
                'name': 'Inspección inicial',
                'step_type': 'action',
                'sequence': 20,
                'position_x': 300,
                'position_y': 100,
                'note': 'Revisar estado general de la motocicleta'
            },
            {
                'service_id': service_id,
                'name': '¿Requiere repuestos?',
                'step_type': 'decision',
                'sequence': 30,
                'position_x': 500,
                'position_y': 100,
                'decision_question': '¿La motocicleta necesita repuestos nuevos?'
            },
            {
                'service_id': service_id,
                'name': 'Fin del Servicio',
                'step_type': 'end',
                'sequence': 40,
                'position_x': 700,
                'position_y': 100,
                'note': 'Servicio completado'
            }
        ]
        
        created_steps = []
        for step_data in steps_data:
            step = self.create(step_data)
            created_steps.append(step)
        
        # Crear conexiones
        if len(created_steps) >= 4:
            created_steps[0].next_step_id = created_steps[1].id  # Inicio -> Inspección
            created_steps[1].next_step_id = created_steps[2].id  # Inspección -> Decisión
            created_steps[2].next_step_yes_id = created_steps[3].id  # Decisión SÍ -> Fin
            created_steps[2].next_step_no_id = created_steps[3].id   # Decisión NO -> Fin
        
        return created_steps