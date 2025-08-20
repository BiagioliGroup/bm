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
    
    linked_task_id = fields.Many2one(
        'project.task',
        string='Tarea Vinculada',
        readonly=True,
        help='Tarea creada desde esta actividad'
    )
    
    @api.model
    def default_get(self, fields_list):
        """Override para agregar proyecto por defecto si está en contexto"""
        defaults = super(MailActivity, self).default_get(fields_list)
        
        # Si estamos en un proyecto, sugerirlo por defecto
        if self._context.get('default_project_id'):
            defaults['project_id'] = self._context.get('default_project_id')
        elif self._context.get('active_model') == 'project.task':
            # Si estamos en una tarea, obtener su proyecto
            task_id = self._context.get('active_id')
            if task_id:
                task = self.env['project.task'].browse(task_id)
                if task.project_id:
                    defaults['project_id'] = task.project_id.id
        elif self._context.get('active_model') == 'project.project':
            # Si estamos en un proyecto
            defaults['project_id'] = self._context.get('active_id')
            
        return defaults
    
    @api.model
    def create(self, vals):
        """Override create para crear tarea si hay proyecto"""
        activity = super(MailActivity, self).create(vals)
        
        # Si hay proyecto, crear tarea automáticamente
        if activity.project_id:
            activity._create_project_task()
            
        return activity
    
    def _create_project_task(self):
        """Crear tarea de proyecto desde la actividad"""
        self.ensure_one()
        
        # Obtener información del recurso
        resource_name = self._get_resource_name()
        
        # Crear la tarea
        task_vals = {
            'name': f"{self.activity_type_id.name}: {resource_name}",
            'project_id': self.project_id.id,
            'user_ids': [(4, self.user_id.id)],
            'date_deadline': self.date_deadline,
            'description': self.note or '',
            'priority': '1',  # Normal
            # Campos personalizados para tracking
            'activity_id': self.id,
            'resource_ref': f"{self.res_model},{self.res_id}",
            'resource_model': self.res_model,
            'resource_id': self.res_id,
            'resource_name': resource_name,
        }
        
        task = self.env['project.task'].create(task_vals)
        self.linked_task_id = task
        
        _logger.info(f"Tarea creada desde actividad: {task.name}")
        
        # Mensaje en el chatter del registro origen
        if self.res_model and self.res_id:
            try:
                record = self.env[self.res_model].browse(self.res_id)
                if hasattr(record, 'message_post'):
                    record.message_post(
                        body=f"""
                        <div class="alert alert-success">
                            <i class="fa fa-check"/> Se creó la tarea 
                            <a href="#" data-oe-model="project.task" data-oe-id="{task.id}">
                                <i class="fa fa-tasks"/> {task.name}
                            </a> 
                            en el proyecto <b>{self.project_id.name}</b>
                        </div>
                        """
                    )
            except Exception as e:
                _logger.warning(f"No se pudo postear mensaje: {e}")
        
        return task
    
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
    
    def action_done(self):
        """Marcar actividad como hecha y actualizar tarea"""
        for activity in self:
            if activity.linked_task_id:
                # Buscar etapa de completado
                done_stage = self.env['project.task.type'].search([
                    ('fold', '=', True)
                ], limit=1)
                
                if done_stage:
                    activity.linked_task_id.stage_id = done_stage
                    
                # Mensaje en el chatter
                activity.linked_task_id.message_post(
                    body=_("✅ Actividad completada")
                )
                
        return super(MailActivity, self).action_done()
    
    def action_view_task(self):
        """Ver la tarea vinculada"""
        self.ensure_one()
        if not self.linked_task_id:
            raise UserError(_('No hay tarea vinculada a esta actividad'))
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tarea',
            'res_model': 'project.task',
            'res_id': self.linked_task_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    @api.model
    def action_schedule_activity(self):
        """Acción para abrir nuestro wizard personalizado"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Programar Actividad',
            'res_model': 'schedule.activity.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': self._context,
        }