# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ScheduleActivityWizard(models.TransientModel):
    """Wizard simplificado para programar actividades con proyectos"""
    _name = 'schedule.activity.wizard'
    _description = 'Programar Actividad con Proyecto'
    
    activity_type_id = fields.Many2one(
        'mail.activity.type',
        string='Tipo de Actividad',
        required=True,
        default=lambda self: self.env.ref('mail.mail_activity_data_todo', False)
    )
    
    summary = fields.Char(
        string='Resumen'
    )
    
    note = fields.Html(
        string='Notas',
        sanitize=True
    )
    
    date_deadline = fields.Date(
        string='Fecha Límite',
        required=True,
        default=fields.Date.context_today
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='Asignado a',
        required=True,
        default=lambda self: self.env.user
    )
    
    project_id = fields.Many2one(
        'project.project',
        string='Proyecto',
        help='Si seleccionás un proyecto, se creará una tarea automáticamente'
    )
    
    create_task = fields.Boolean(
        string='Se creará una tarea',
        compute='_compute_create_task',
        store=False
    )
    
    @api.depends('project_id')
    def _compute_create_task(self):
        """Indicar si se creará tarea"""
        for wizard in self:
            wizard.create_task = bool(wizard.project_id)
    
    def action_schedule(self):
        """Programar la actividad"""
        self.ensure_one()
        
        # Obtener contexto
        active_model = self._context.get('active_model') or self._context.get('default_res_model')
        active_id = self._context.get('active_id') or self._context.get('default_res_id')
        
        if not active_model or not active_id:
            raise UserError(_('No se puede determinar el registro activo'))
        
        # Crear la actividad
        activity_vals = {
            'activity_type_id': self.activity_type_id.id,
            'summary': self.summary or self.activity_type_id.name,
            'note': self.note,
            'date_deadline': self.date_deadline,
            'user_id': self.user_id.id,
            'res_model': active_model,
            'res_id': active_id,
            'project_id': self.project_id.id if self.project_id else False,
        }
        
        activity = self.env['mail.activity'].create(activity_vals)
        
        # Mensaje de confirmación
        if activity.linked_task_id:
            message = _('✅ Actividad programada y tarea #%s creada en proyecto %s') % (
                activity.linked_task_id.id, 
                self.project_id.name
            )
        else:
            message = _('✅ Actividad programada correctamente')
        
        # Notificación
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Éxito'),
                'message': message,
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
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