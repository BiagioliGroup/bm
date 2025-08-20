# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


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
    
    deadline_time = fields.Float(
        string='Hora',
        help='Hora específica (formato 24h, ej: 14.5 = 14:30)',
        default=9.0  # 9:00 AM por defecto
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
        _logger.info("🟪 BIAGIOLI WIZARD: Iniciando action_schedule()")
        
        # Obtener contexto
        active_model = self._context.get('active_model') or self._context.get('default_res_model')
        active_id = self._context.get('active_id') or self._context.get('default_res_id')
        
        _logger.info(f"🟪 BIAGIOLI WIZARD: active_model: {active_model}")
        _logger.info(f"🟪 BIAGIOLI WIZARD: active_id: {active_id}")
        _logger.info(f"🟪 BIAGIOLI WIZARD: project_id: {self.project_id}")
        _logger.info(f"🟪 BIAGIOLI WIZARD: project_id.id: {self.project_id.id if self.project_id else None}")
        
        if not active_model or not active_id:
            _logger.error("🟪 BIAGIOLI WIZARD: No se puede determinar el registro activo")
            raise UserError(_('No se puede determinar el registro activo'))
        
        # Crear la actividad
        activity_vals = {
            'activity_type_id': self.activity_type_id.id,
            'summary': self.summary or self.activity_type_id.name,
            'note': self.note,
            'date_deadline': self.date_deadline,
            'deadline_time': self.deadline_time,
            'user_id': self.user_id.id,
            'res_model': active_model,
            'res_id': active_id,
            'project_id': self.project_id.id if self.project_id else False,
        }
        
        _logger.info(f"🟪 BIAGIOLI WIZARD: activity_vals: {activity_vals}")
        
        activity = self.env['mail.activity'].create(activity_vals)
        _logger.info(f"🟪 BIAGIOLI WIZARD: Actividad creada con ID: {activity.id}")
        
        # Verificar inmediatamente si se creó la tarea
        if activity.linked_task_id:
            _logger.info(f"🟪 BIAGIOLI WIZARD: ¡Tarea creada! ID: {activity.linked_task_id.id}")
        else:
            _logger.warning(f"🟪 BIAGIOLI WIZARD: No se creó tarea para actividad #{activity.id}")
        
        # Mensaje de confirmación
        if activity.linked_task_id:
            message = _('✅ Actividad programada y tarea #%s creada en proyecto %s') % (
                activity.linked_task_id.id, 
                self.project_id.name
            )
        else:
            message = _('✅ Actividad programada correctamente')
        
        _logger.info(f"🟪 BIAGIOLI WIZARD: Mensaje final: {message}")
        
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