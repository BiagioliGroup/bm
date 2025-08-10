# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class MotorcycleService(models.Model):
    _name = 'motorcycle.service'
    _description = 'Servicio de Motocicleta'
    _rec_name = 'name'

    name = fields.Char(
        string='Número de Servicio',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('motorcycle.service.sequence') or 'Nuevo'
    )
    motorcycle_ids = fields.Many2many(
        'motorcycle.motorcycle',
        'motorcycle_service_rel',
        'service_id', 'motorcycle_id',
        string='Motocicletas',
        required=True
    )
    description = fields.Text(string='Descripción')
    labor_description = fields.Text(string='Descripción del Trabajo')

    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        default=lambda self: self.env.company.currency_id
    )

    service_line_ids = fields.One2many(
        'motorcycle.service.line',
        'service_id',
        string='Líneas del Servicio'
    )

    total_parts_cost = fields.Monetary(
        string='Costo de Repuestos',
        currency_field='currency_id',
        compute='_compute_totals',
        store=True,
        default=0.0
    )
    total_services_cost = fields.Monetary(
        string='Costo de Mano de Obra',
        currency_field='currency_id',
        compute='_compute_totals',
        store=True,
        default=0.0
    )
    total_service_cost = fields.Monetary(
        string='Costo Total',
        currency_field='currency_id',
        compute='_compute_totals',
        store=True,
        default=0.0
    )

    step_ids = fields.One2many(
        'motorcycle.service.step',
        'service_id',
        string='Pasos del Servicio'
    )

    @api.depends('service_line_ids.subtotal', 'service_line_ids.product_id.type')
    def _compute_totals(self):
        for service in self:
            parts_total = 0.0
            services_total = 0.0
            for line in service.service_line_ids:
                if line.display_type == 'line' and line.product_id:
                    if line.product_id.type == 'consu':
                        parts_total += line.subtotal
                    elif line.product_id.type == 'service':
                        services_total += line.subtotal
            service.total_parts_cost = parts_total
            service.total_services_cost = services_total
            service.total_service_cost = parts_total + services_total

    def action_print_service_report(self):
        """Método para imprimir reporte del servicio"""
        self.ensure_one()
        # Placeholder para futuro reporte personalizado
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reporte de Servicio',
            'res_model': 'motorcycle.service',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_motorcycles(self):
        """Método para ver las motocicletas del servicio"""
        self.ensure_one()
        motorcycles = self.motorcycle_ids
        
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Motocicletas del Servicio %s' % self.name,
            'res_model': 'motorcycle.motorcycle',
            'domain': [('id', 'in', motorcycles.ids)],
            'context': {},
        }
        
        if len(motorcycles) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': motorcycles.id,
            })
        else:
            action.update({
                'view_mode': 'kanban,list,form',
            })
            
        return action

    def action_view_service_lines(self):
        """Método para ver las líneas del servicio"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Líneas del Servicio %s' % self.name,
            'res_model': 'motorcycle.service.line',
            'view_mode': 'list,form',
            'domain': [('service_id', '=', self.id)],
            'context': {
                'default_service_id': self.id,
            },
        }

    def action_open_workflow_designer(self):
        """Abrir el diseñador de workflow en ventana separada"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Diseñador de Workflow - %s' % self.name,
            'res_model': 'motorcycle.service',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('sh_motorcycle_backend.view_motorcycle_service_workflow_designer').id,
            'target': 'new',
            'context': {
                'default_service_id': self.id,
                'workflow_mode': True,
            },
        }

    def create_workflow_template(self):
        """Crear plantilla básica de workflow"""
        self.ensure_one()
        
        # Eliminar pasos existentes si los hay
        self.step_ids.unlink()
        
        # Datos de la plantilla
        steps_data = [
            {
                'service_id': self.id,
                'name': 'Inicio del Servicio',
                'step_type': 'start',
                'sequence': 10,
                'position_x': 50,
                'position_y': 50,
                'note': 'Punto de inicio del proceso de servicio técnico'
            },
            {
                'service_id': self.id,
                'name': 'Inspección Visual General',
                'step_type': 'action',
                'sequence': 20,
                'position_x': 300,
                'position_y': 50,
                'note': 'Revisar estado general de la motocicleta, carrocería, luces, etc.'
            },
            {
                'service_id': self.id,
                'name': 'Revisión del Motor',
                'step_type': 'action',
                'sequence': 30,
                'position_x': 550,
                'position_y': 50,
                'note': 'Verificar niveles de aceite, refrigerante, filtros'
            },
            {
                'service_id': self.id,
                'name': '¿Requiere Cambio de Aceite?',
                'step_type': 'decision',
                'sequence': 40,
                'position_x': 300,
                'position_y': 200,
                'decision_question': '¿El aceite está sucio o ha cumplido su ciclo de mantenimiento?',
                'note': 'Evaluar color, viscosidad y kilometraje'
            },
            {
                'service_id': self.id,
                'name': 'Cambiar Aceite y Filtro',
                'step_type': 'action',
                'sequence': 50,
                'position_x': 50,
                'position_y': 350,
                'note': 'Drenar aceite usado, cambiar filtro, agregar aceite nuevo'
            },
            {
                'service_id': self.id,
                'name': 'Revisar Sistema de Frenos',
                'step_type': 'action',
                'sequence': 60,
                'position_x': 550,
                'position_y': 350,
                'note': 'Verificar pastillas, discos, nivel de líquido de frenos'
            },
            {
                'service_id': self.id,
                'name': '¿Requiere Repuestos?',
                'step_type': 'decision',
                'sequence': 70,
                'position_x': 300,
                'position_y': 500,
                'decision_question': '¿Se necesitan repuestos o componentes nuevos?',
                'note': 'Evaluar desgaste de componentes críticos'
            },
            {
                'service_id': self.id,
                'name': 'Cotizar y Solicitar Aprobación',
                'step_type': 'action',
                'sequence': 80,
                'position_x': 50,
                'position_y': 650,
                'note': 'Preparar cotización de repuestos y solicitar autorización del cliente'
            },
            {
                'service_id': self.id,
                'name': 'Prueba Final',
                'step_type': 'action',
                'sequence': 90,
                'position_x': 550,
                'position_y': 650,
                'note': 'Probar funcionamiento general, luces, frenos, motor'
            },
            {
                'service_id': self.id,
                'name': 'Entrega al Cliente',
                'step_type': 'end',
                'sequence': 100,
                'position_x': 300,
                'position_y': 800,
                'note': 'Explicar trabajo realizado y entregar motocicleta'
            }
        ]
        
        # Crear los pasos
        created_steps = []
        for step_data in steps_data:
            step = self.env['motorcycle.service.step'].create(step_data)
            created_steps.append(step)
        
        # Establecer conexiones del flujo
        if len(created_steps) >= 10:
            # Conexiones lineales principales
            created_steps[0].next_step_id = created_steps[1].id  # Inicio -> Inspección
            created_steps[1].next_step_id = created_steps[2].id  # Inspección -> Motor
            created_steps[2].next_step_id = created_steps[3].id  # Motor -> ¿Aceite?
            
            # Conexiones de decisión: ¿Aceite?
            created_steps[3].next_step_yes_id = created_steps[4].id  # SÍ -> Cambiar aceite
            created_steps[3].next_step_no_id = created_steps[5].id   # NO -> Revisar frenos
            
            # Flujo después del cambio de aceite
            created_steps[4].next_step_id = created_steps[5].id  # Aceite -> Frenos
            
            # Continuar con segunda decisión
            created_steps[5].next_step_id = created_steps[6].id  # Frenos -> ¿Repuestos?
            
            # Conexiones de decisión: ¿Repuestos?
            created_steps[6].next_step_yes_id = created_steps[7].id  # SÍ -> Cotizar
            created_steps[6].next_step_no_id = created_steps[8].id   # NO -> Prueba final
            
            # Flujo final
            created_steps[7].next_step_id = created_steps[8].id  # Cotizar -> Prueba
            created_steps[8].next_step_id = created_steps[9].id  # Prueba -> Entrega
        
        # Mostrar mensaje de confirmación
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Plantilla de Workflow Creada',
                'message': 'Se ha creado una plantilla básica con %d pasos. Puedes personalizarla según tus necesidades.' % len(created_steps),
                'type': 'success',
                'sticky': False,
            }
        }