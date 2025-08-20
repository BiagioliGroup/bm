# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class ScheduleActivityWizard(models.TransientModel):
    _name = 'schedule.activity.wizard'
    _description = 'Wizard para Programar Actividades con Proyecto'
    
    # Campos de la actividad
    activity_type_id = fields.Many2one(
        'mail.activity.type',
        string='Tipo de Actividad',
        required=True
    )
    
    summary = fields.Char(
        string='Resumen',
        required=True
    )
    
    date_deadline = fields.Date(
        string='Fecha Límite',
        required=True,
        default=fields.Date.today
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='Asignado a',
        required=True,
        default=lambda self: self.env.user
    )
    
    note = fields.Html(
        string='Descripción'
    )
    
    # Campo para proyecto
    project_id = fields.Many2one(
        'project.project',
        string='Proyecto',
        help='Si se selecciona un proyecto, se creará una tarea automáticamente'
    )
    
    # Campos de contexto (hidden)
    res_model = fields.Char(string='Modelo del Recurso')
    res_id = fields.Integer(string='ID del Recurso')
    
    @api.model
    def default_get(self, fields_list):
        """Obtener valores por defecto desde el contexto"""
        defaults = super().default_get(fields_list)
        
        context = self.env.context
        
        # Obtener modelo y ID del contexto
        if context.get('active_model'):
            defaults['res_model'] = context['active_model']
        if context.get('active_id'):
            defaults['res_id'] = context['active_id']
            
        # Si viene de un proyecto, pre-seleccionarlo
        if context.get('active_model') == 'project.project' and context.get('active_id'):
            defaults['project_id'] = context['active_id']
            
        return defaults
    
    def action_schedule(self):
        """Programar la actividad"""
        self.ensure_one()
        
        # Obtener contexto
        active_model = self._context.get('active_model') or self._context.get('default_res_model')
        active_id = self._context.get('active_id') or self._context.get('default_res_id')
        
        # Validaciones
        if not active_model or not active_id:
            raise UserError(_('No se puede determinar el registro origen'))
        
        # Buscar el modelo en ir.model
        model_record = self.env['ir.model'].search([('model', '=', active_model)], limit=1)
        if not model_record:
            raise UserError(_('No se encontró el modelo %s') % active_model)
            
        # Crear la actividad con todos los campos obligatorios
        activity_vals = {
            'activity_type_id': self.activity_type_id.id,
            'summary': self.summary or self.activity_type_id.name,
            'date_deadline': self.date_deadline,
            'user_id': self.user_id.id,
            'res_model': active_model,
            'res_model_id': model_record.id,  # Campo obligatorio
            'res_id': active_id,
            'note': self.note,
        }
        
        # Si hay proyecto, agregarlo a la actividad
        if self.project_id:
            activity_vals['project_id'] = self.project_id.id
            
        activity = self.env['mail.activity'].sudo().create(activity_vals)
        
        # Mensaje de éxito
        message = _('✅ Actividad programada correctamente')
        if self.project_id and hasattr(activity, 'linked_task_id') and activity.linked_task_id:
            message = _('✅ Actividad programada y tarea creada en proyecto %s') % self.project_id.name
        
        # Notificación de éxito
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