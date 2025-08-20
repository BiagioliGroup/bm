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
        
        # Forzar notificación móvil
        self._force_mobile_notification(activity)

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
    
    def _force_mobile_notification(self, activity):
        """Forzar notificación que llegue al móvil"""
        try:
            # 1. Crear mensaje en bandeja de entrada
            message_body = f'''
                <div style="padding: 12px; background: #e7f5ff; border-left: 4px solid #007bff; border-radius: 4px; margin: 8px 0;">
                    <h4 style="margin: 0 0 8px 0; color: #007bff;">🎯 Nueva Actividad Programada</h4>
                    <p style="margin: 4px 0;"><strong>Actividad:</strong> {activity.summary}</p>
                    <p style="margin: 4px 0;"><strong>Fecha límite:</strong> {activity.date_deadline}</p>
                    <p style="margin: 4px 0;"><strong>Asignado a:</strong> {activity.user_id.name}</p>
                    {f'<p style="margin: 4px 0;"><strong>Proyecto:</strong> {activity.project_id.name}</p>' if activity.project_id else ''}
                    {f'<p style="margin: 4px 0;"><strong>Tarea creada:</strong> #{activity.linked_task_id.id} - {activity.linked_task_id.name}</p>' if hasattr(activity, 'linked_task_id') and activity.linked_task_id else ''}
                </div>
            '''
            
            message = self.env['mail.message'].sudo().create({
                'message_type': 'notification',
                'body': message_body,
                'subject': f'📋 Nueva Actividad: {activity.summary}',
                'author_id': self.env.user.partner_id.id,
                'partner_ids': [(4, activity.user_id.partner_id.id)],
                'needaction': True,
                'model': activity.res_model,
                'res_id': activity.res_id,
            })
            
            # 2. Enviar por bus para notificación inmediata
            notification_message = f'{activity.summary}'
            if activity.project_id:
                notification_message += f' (Proyecto: {activity.project_id.name})'
            if hasattr(activity, 'linked_task_id') and activity.linked_task_id:
                notification_message += f' - Tarea #{activity.linked_task_id.id} creada'
                
            self.env['bus.bus']._sendone(
                f'res.partner_{activity.user_id.partner_id.id}',
                'simple_notification',
                {
                    'title': '🎯 Actividad Programada',
                    'message': notification_message,
                    'type': 'success',
                    'sticky': True,
                }
            )
            
            # 3. Log para debug
            _logger.info(f"📱 Notificación móvil enviada para actividad #{activity.id} a usuario {activity.user_id.name}")
            
            # 4. Commit para asegurar que se guarde
            self.env.cr.commit()
            
        except Exception as e:
            _logger.warning(f"⚠️ Error enviando notificación móvil: {e}")
    
    def _send_push_notification(self, activity):
        """Método legacy - usar _force_mobile_notification en su lugar"""
        return self._force_mobile_notification(activity)