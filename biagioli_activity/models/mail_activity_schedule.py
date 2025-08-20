# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class MailActivitySchedule(models.TransientModel):
    """Extiende el wizard estándar de actividades para agregar proyecto"""
    _inherit = 'mail.activity.schedule'
    
    # Campo adicional para proyecto
    project_id = fields.Many2one(
        'project.project',
        string='Proyecto',
        help='Si seleccionás un proyecto, se creará una tarea automáticamente'
    )
    
    will_create_task = fields.Boolean(
        string='Se creará tarea',
        compute='_compute_will_create_task'
    )
    
    @api.depends('project_id')
    def _compute_will_create_task(self):
        """Indicar si se creará una tarea"""
        for wizard in self:
            wizard.will_create_task = bool(wizard.project_id)
    
    @api.model
    def default_get(self, fields_list):
        """Sugerir proyecto por defecto si estamos en contexto de proyecto"""
        defaults = super().default_get(fields_list)
        
        # Si estamos en una tarea, obtener su proyecto
        if self._context.get('active_model') == 'project.task':
            task_id = self._context.get('active_id')
            if task_id:
                task = self.env['project.task'].browse(task_id)
                if task.exists() and task.project_id:
                    defaults['project_id'] = task.project_id.id
                    
        # Si estamos en un proyecto
        elif self._context.get('active_model') == 'project.project':
            project_id = self._context.get('active_id')
            if project_id:
                defaults['project_id'] = project_id
                
        return defaults
    
    def _prepare_activities(self):
        """Override para agregar proyecto a las actividades"""
        activities_values = super()._prepare_activities()
        
        # Agregar proyecto a cada actividad si está definido
        if self.project_id:
            for activity_vals in activities_values:
                activity_vals['project_id'] = self.project_id.id
                
        return activities_values
    
    def action_schedule_activities(self):
        """Override del botón Programar"""
        result = super().action_schedule_activities()
        
        # Mostrar notificación si se crearon tareas
        if self.project_id:
            # Contar actividades creadas
            activities = self.env['mail.activity'].search([
                ('res_model', '=', self.res_model),
                ('res_id', 'in', self.res_ids),
                ('project_id', '=', self.project_id.id),
                ('create_uid', '=', self.env.uid),
            ], order='create_date desc', limit=10)
            
            tasks_created = activities.mapped('linked_task_id')
            if tasks_created:
                message = _('✅ Se crearon %d tareas en el proyecto %s') % (
                    len(tasks_created), 
                    self.project_id.name
                )
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Tareas Creadas'),
                        'message': message,
                        'type': 'success',
                        'sticky': False,
                    }
                }
        
        return result
    
    def action_schedule_activities_done(self):
        """Override del botón Programar y marcar como hecho"""
        result = super().action_schedule_activities_done()
        
        # Notificación si se crearon tareas
        if self.project_id:
            message = _('✅ Actividades marcadas como hechas y tareas creadas en %s') % self.project_id.name
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Completado'),
                    'message': message,
                    'type': 'success',
                    'sticky': False,
                }
            }
            
        return result