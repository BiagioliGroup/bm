# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ScheduleActivityWizard(models.TransientModel):
    """Wizard para programar actividades con integración de proyectos"""
    _name = 'schedule.activity.wizard'
    _inherit = 'mail.activity.schedule'
    _description = 'Programar Actividad con Integración de Proyectos'
    
    # Hereda campos del wizard estándar y agrega los propios
    project_id = fields.Many2one(
        'project.project',
        string='Proyecto',
        help='Opcional: Vincular esta actividad a un proyecto para crear una tarea'
    )
    
    create_task = fields.Boolean(
        string='Crear Tarea',
        compute='_compute_create_flags',
        store=True,
        help='Se creará una tarea si se selecciona un proyecto'
    )
    
    create_todo = fields.Boolean(
        string='Crear To-Do',
        compute='_compute_create_flags',
        store=True,
        help='Se creará un to-do si no se selecciona un proyecto'
    )
    
    action_type = fields.Selection([
        ('schedule', 'Programar'),
        ('schedule_done', 'Programar y Marcar como Hecho'),
        ('done_schedule_next', 'Completar y Programar Siguiente'),
    ], string='Acción', default='schedule', required=True)
    
    @api.depends('project_id')
    def _compute_create_flags(self):
        """Calcular qué se va a crear según el proyecto"""
        for wizard in self:
            user = self.env.user
            is_project_user = user.has_group('project.group_project_user')
            is_project_manager = user.has_group('project.group_project_manager')
            
            if wizard.project_id and (is_project_user or is_project_manager):
                wizard.create_task = True
                wizard.create_todo = False
            else:
                wizard.create_task = False
                wizard.create_todo = True
    
    def action_schedule_activity(self):
        """Acción principal para programar actividad"""
        self.ensure_one()
        
        # Validar datos
        if not self.activity_type_id:
            raise UserError(_('Por favor seleccione un tipo de actividad.'))
        
        # Obtener el modelo y registro desde el contexto
        active_model = self._context.get('active_model')
        active_ids = self._context.get('active_ids', [])
        
        if not active_model or not active_ids:
            raise UserError(_('No hay registros seleccionados.'))
        
        # Crear actividades para cada registro seleccionado
        activities = self.env['mail.activity']
        
        for record_id in active_ids:
            # Preparar valores de la actividad
            activity_vals = {
                'activity_type_id': self.activity_type_id.id,
                'summary': self.summary or self.activity_type_id.name,
                'note': self.note,
                'date_deadline': self.date_deadline,
                'user_id': self.user_id.id,
                'res_model': active_model,
                'res_id': record_id,
                'project_id': self.project_id.id if self.project_id else False,
                'create_task': self.create_task,
                'create_todo': self.create_todo,
            }
            
            # Crear la actividad
            activity = activities.create(activity_vals)
            activities |= activity
        
        # Ejecutar acción según el tipo
        if self.action_type == 'schedule_done':
            # Marcar como completada inmediatamente
            activities.action_done()
            
        elif self.action_type == 'done_schedule_next':
            # Completar y programar siguiente
            activities.action_done_schedule_next()
        
        # Mensaje de confirmación
        message = _('Actividad programada exitosamente.')
        if self.create_task:
            message = _('Actividad programada y tarea creada.')
        elif self.create_todo:
            message = _('Actividad programada y to-do creado.')
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Éxito'),
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_schedule_and_close(self):
        """Programar y cerrar el wizard"""
        self.action_schedule_activity()
        return {'type': 'ir.actions.act_window_close'}
    
    def action_schedule_done_and_close(self):
        """Programar, marcar como hecho y cerrar"""
        self.action_type = 'schedule_done'
        self.action_schedule_activity()
        return {'type': 'ir.actions.act_window_close'}
    
    def action_done_schedule_next_and_close(self):
        """Completar, programar siguiente y cerrar"""
        self.action_type = 'done_schedule_next'
        self.action_schedule_activity()
        return {'type': 'ir.actions.act_window_close'}