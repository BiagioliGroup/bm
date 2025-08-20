# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class MailActivity(models.Model):
    """Extiende mail.activity para agregar integración con proyectos"""
    _inherit = 'mail.activity'
    
    # Campos adicionales para la integración
    project_id = fields.Many2one(
        'project.project',
        string='Proyecto',
        help='Proyecto al cual vincular esta actividad'
    )
    
    create_task = fields.Boolean(
        string='Crear Tarea',
        default=False,
        help='Crear una tarea de proyecto al programar esta actividad'
    )
    
    create_todo = fields.Boolean(
        string='Crear To-Do',
        default=False,
        help='Crear un to-do al programar esta actividad'
    )
    
    linked_task_id = fields.Many2one(
        'project.task',
        string='Tarea Vinculada',
        readonly=True,
        help='Tarea creada desde esta actividad'
    )
    
    linked_todo_id = fields.Many2one(
        'project.todo',
        string='To-Do Vinculado',
        readonly=True,
        help='To-Do creado desde esta actividad'
    )
    
    @api.model
    def create(self, vals):
        """Override create to handle task/todo creation"""
        activity = super(MailActivity, self).create(vals)
        
        # Crear tarea o to-do según configuración
        if activity.create_task or activity.create_todo:
            activity._create_linked_items()
            
        return activity
    
    def action_done(self):
        """Override action_done to handle linked items"""
        # Marcar tareas/todos relacionados como completados
        for activity in self:
            if activity.linked_task_id:
                activity.linked_task_id.write({
                    'stage_id': self.env['project.task.type'].search([
                        ('fold', '=', True)
                    ], limit=1).id or activity.linked_task_id.stage_id.id,
                    'date_end': fields.Datetime.now(),
                })
            
            if activity.linked_todo_id:
                activity.linked_todo_id.write({
                    'state': 'done',
                    'date_done': fields.Datetime.now(),
                })
        
        return super(MailActivity, self).action_done()
    
    def action_done_schedule_next(self):
        """Override para manejar la creación de siguiente actividad"""
        result = super(MailActivity, self).action_done_schedule_next()
        
        # Si se creó una nueva actividad, copiar configuración de proyecto
        if self.project_id:
            # La nueva actividad hereda el proyecto
            next_activity = self.search([
                ('res_model', '=', self.res_model),
                ('res_id', '=', self.res_id),
                ('user_id', '=', self.user_id),
            ], order='create_date desc', limit=1)
            
            if next_activity:
                next_activity.project_id = self.project_id
                next_activity._create_linked_items()
        
        return result
    
    def _create_linked_items(self):
        """Crear tarea y/o to-do según configuración del usuario"""
        self.ensure_one()
        
        user = self.user_id or self.env.user
        
        # Determinar qué crear según el tipo de usuario
        is_project_user = user.has_group('project.group_project_user')
        is_project_manager = user.has_group('project.group_project_manager')
        
        # Preparar valores comunes
        resource_ref = f"{self.res_model},{self.res_id}"
        resource_name = self._get_resource_name()
        
        common_vals = {
            'name': f"{self.activity_type_id.name}: {resource_name}",
            'description': self.note or '',
            'user_ids': [(4, user.id)],
            'date_deadline': self.date_deadline,
            'resource_ref': resource_ref,
            'resource_model': self.res_model,
            'resource_id': self.res_id,
            'resource_name': resource_name,
            'activity_id': self.id,
        }
        
        # Crear tarea si es usuario de proyecto y hay proyecto seleccionado
        if (is_project_user or is_project_manager) and self.project_id:
            task_vals = common_vals.copy()
            task_vals.update({
                'project_id': self.project_id.id,
                'priority': '1',  # Normal priority
            })
            
            task = self.env['project.task'].create(task_vals)
            self.linked_task_id = task
            
            _logger.info(f"Tarea creada desde actividad: {task.name}")
        
        # Crear to-do si no hay proyecto o si es usuario interno
        elif not self.project_id or not (is_project_user or is_project_manager):
            todo_vals = common_vals.copy()
            todo_vals.update({
                'state': 'open',
                'priority': 'normal',
            })
            
            todo = self.env['project.todo'].create(todo_vals)
            self.linked_todo_id = todo
            
            _logger.info(f"To-Do creado desde actividad: {todo.name}")
        
        # Si es usuario de proyecto sin proyecto, crear ambos
        elif (is_project_user or is_project_manager) and not self.project_id:
            # Crear tarea sin proyecto
            task_vals = common_vals.copy()
            task_vals.update({
                'priority': '1',
            })
            task = self.env['project.task'].create(task_vals)
            self.linked_task_id = task
            
            # Crear to-do también
            todo_vals = common_vals.copy()
            todo_vals.update({
                'state': 'open',
                'priority': 'normal',
            })
            todo = self.env['project.todo'].create(todo_vals)
            self.linked_todo_id = todo
            
            _logger.info(f"Tarea y To-Do creados desde actividad")
    
    def _get_resource_name(self):
        """Obtener el nombre del recurso relacionado"""
        self.ensure_one()
        
        try:
            record = self.env[self.res_model].browse(self.res_id)
            if hasattr(record, 'display_name'):
                return record.display_name
            elif hasattr(record, 'name'):
                return record.name
            else:
                return f"{self.res_model}({self.res_id})"
        except:
            return f"{self.res_model}({self.res_id})"
    
    @api.onchange('project_id')
    def _onchange_project_id(self):
        """Actualizar flags según proyecto seleccionado"""
        if self.project_id:
            self.create_task = True
            self.create_todo = False
        else:
            self.create_task = False
            self.create_todo = True