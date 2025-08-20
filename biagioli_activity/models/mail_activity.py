# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class MailActivity(models.Model):
    """Extiende mail.activity para agregar integración con proyectos"""
    _inherit = 'mail.activity'
    
    # Campos adicionales
    project_id = fields.Many2one(
        'project.project',
        string='Proyecto',
        help='Proyecto vinculado a esta actividad'
    )
    
    linked_task_id = fields.Many2one(
        'project.task',
        string='Tarea Vinculada',
        readonly=True,
        help='Tarea creada desde esta actividad'
    )
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override para crear tareas cuando hay proyecto"""
        activities = super().create(vals_list)
        
        for activity in activities:
            if activity.project_id and not activity.linked_task_id:
                activity._create_project_task()
                
        return activities
    
    def _create_project_task(self):
        """Crear tarea de proyecto desde la actividad"""
        self.ensure_one()
        
        if not self.project_id:
            return False
            
        # Obtener información del recurso
        resource_name = self._get_resource_name()
        
        # Crear la tarea
        task_vals = {
            'name': f"{self.activity_type_id.name}: {resource_name}",
            'project_id': self.project_id.id,
            'user_ids': [(4, self.user_id.id)],
            'date_deadline': self.date_deadline,
            'description': self.note or '',
            'priority': '1',
        }
        
        task = self.env['project.task'].create(task_vals)
        self.linked_task_id = task
        
        _logger.info(f"Tarea #{task.id} creada desde actividad para {resource_name}")
        
        # Mensaje en el chatter
        self._post_task_creation_message(task)
        
        return task
    
    def _get_resource_name(self):
        """Obtener el nombre del recurso"""
        self.ensure_one()
        try:
            record = self.env[self.res_model].browse(self.res_id)
            return record.display_name if record.exists() else f"{self.res_model}#{self.res_id}"
        except:
            return f"{self.res_model}#{self.res_id}"
    
    def _post_task_creation_message(self, task):
        """Postear mensaje sobre la tarea creada"""
        try:
            if self.res_model and self.res_id:
                record = self.env[self.res_model].browse(self.res_id)
                if record.exists() and hasattr(record, 'message_post'):
                    record.message_post(
                        body=f"""
                        <div style="margin: 10px 0;">
                            <i class="fa fa-check text-success"/> 
                            Tarea creada: <a href="#" data-oe-model="project.task" data-oe-id="{task.id}">
                                <i class="fa fa-tasks"/> {task.name}
                            </a>
                            en proyecto <b>{self.project_id.name}</b>
                        </div>
                        """,
                        message_type='notification',
                        subtype_xmlid='mail.mt_note',
                    )
        except Exception as e:
            _logger.warning(f"No se pudo postear mensaje: {e}")
    
    def action_done(self):
        """Marcar actividad como completada y actualizar tarea"""
        for activity in self:
            if activity.linked_task_id:
                # Buscar etapa de completado
                done_stage = self.env['project.task.type'].search([
                    ('fold', '=', True),
                    '|',
                    ('project_ids', '=', False),
                    ('project_ids', 'in', activity.project_id.id)
                ], limit=1)
                
                if done_stage:
                    activity.linked_task_id.stage_id = done_stage
                    
        return super().action_done()