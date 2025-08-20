# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class MailActivity(models.Model):
    """Extiende mail.activity para agregar integración con proyectos"""
    _inherit = 'mail.activity'
    
    # Campo para vincular con proyecto
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
                # Marcar tarea como completada
                done_stage = self.env['project.task.type'].search([
                    ('fold', '=', True),
                    ('project_ids', 'in', activity.project_id.id)
                ], limit=1)
                
                if done_stage:
                    activity.linked_task_id.stage_id = done_stage
                
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