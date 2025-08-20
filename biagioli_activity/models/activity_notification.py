# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class MailActivity(models.Model):
    """Extender mail.activity para agregar notificaciones"""
    _inherit = 'mail.activity'
    
    # Campos para control de notificaciones
    notification_sent = fields.Boolean(
        string='Notificación Enviada',
        default=False,
        help='Indica si ya se envió la notificación de vencimiento'
    )
    
    reminder_time = fields.Selection([
        ('15', '15 minutos antes'),
        ('30', '30 minutos antes'),
        ('60', '1 hora antes'),
        ('120', '2 horas antes'),
        ('240', '4 horas antes'),
        ('480', '8 horas antes'),
        ('1440', '1 día antes'),
    ], string='Recordatorio', default='60', help='Cuándo enviar la notificación')
    
    @api.model
    def _send_activity_notifications(self):
        """Método ejecutado por cron para enviar notificaciones"""
        _logger.info("🔔 BIAGIOLI: Iniciando envío de notificaciones de actividades")
        
        # Buscar actividades que necesitan notificación
        activities_to_notify = self._get_activities_for_notification()
        
        if not activities_to_notify:
            _logger.info("🔔 BIAGIOLI: No hay actividades para notificar")
            return
            
        _logger.info(f"🔔 BIAGIOLI: Encontradas {len(activities_to_notify)} actividades para notificar")
        
        # Enviar notificaciones
        for activity in activities_to_notify:
            try:
                self._send_notification(activity)
                activity.notification_sent = True
                _logger.info(f"✅ BIAGIOLI: Notificación enviada para actividad #{activity.id}")
            except Exception as e:
                _logger.error(f"❌ BIAGIOLI: Error enviando notificación para actividad #{activity.id}: {e}")
    
    def _get_activities_for_notification(self):
        """Obtener actividades que necesitan notificación"""
        now = datetime.now()
        
        # Buscar actividades activas con hora específica
        domain = [
            ('date_deadline', '>=', now.date()),  # Solo futuras o de hoy
            ('deadline_time', '!=', False),      # Que tengan hora específica
            ('notification_sent', '=', False),   # Que no se haya enviado notificación
            ('user_id', '!=', False),           # Que tengan usuario asignado
        ]
        
        activities = self.search(domain)
        activities_to_notify = []
        
        for activity in activities:
            if activity._should_send_notification(now):
                activities_to_notify.append(activity)
        
        return activities_to_notify
    
    def _should_send_notification(self, current_time):
        """Verificar si es momento de enviar notificación"""
        if not self.deadline_time or not self.reminder_time:
            return False
            
        # Convertir hora de actividad a datetime
        hours = int(self.deadline_time)
        minutes = int((self.deadline_time - hours) * 60)
        
        activity_datetime = datetime.combine(
            self.date_deadline,
            datetime.min.time().replace(hour=hours, minute=minutes)
        )
        
        # Calcular momento de notificación
        reminder_minutes = int(self.reminder_time)
        notification_time = activity_datetime - timedelta(minutes=reminder_minutes)
        
        # Verificar si es momento de notificar (con margen de 5 minutos)
        time_diff = abs((current_time - notification_time).total_seconds())
        return time_diff <= 300  # 5 minutos de margen
    
    def _send_notification(self, activity):
        """Enviar notificación de vencimiento"""
        
        # 1. Notificación interna de Odoo
        self._send_internal_notification(activity)
        
        # 2. Email (opcional)
        if activity.user_id.email:
            self._send_email_notification(activity)
    
    def _send_internal_notification(self, activity):
        """Enviar notificación interna de Odoo"""
        try:
            # Crear notificación en el bus de Odoo
            self.env['bus.bus']._sendone(
                (self._cr.dbname, 'res.partner', activity.user_id.partner_id.id),
                'simple_notification',
                {
                    'title': _('🔔 Actividad próxima a vencer'),
                    'message': f"📅 {activity.summary or activity.activity_type_id.name}\n"
                              f"🕐 Vence a las {activity.deadline_time:02.0f}:00 hs\n"
                              f"📄 {activity._get_resource_name()}",
                    'type': 'warning',
                    'sticky': True,
                }
            )
            
            # También crear actividad de seguimiento
            if activity.res_model and activity.res_id:
                record = self.env[activity.res_model].browse(activity.res_id)
                if record.exists() and hasattr(record, 'message_post'):
                    record.message_post(
                        body=f"""
                        <div class="alert alert-warning">
                            <h4>🔔 Recordatorio de Actividad</h4>
                            <p><strong>{activity.summary or activity.activity_type_id.name}</strong></p>
                            <p>📅 Vence hoy a las <strong>{activity.deadline_time:02.0f}:00 hs</strong></p>
                            <p>👤 Asignado a: {activity.user_id.name}</p>
                        </div>
                        """,
                        message_type='notification',
                        subtype_xmlid='mail.mt_note',
                    )
        except Exception as e:
            _logger.error(f"Error enviando notificación interna: {e}")
    
    def _send_email_notification(self, activity):
        """Enviar email de notificación"""
        try:
            # Preparar valores del email
            subject = f"🔔 Recordatorio: {activity.summary or activity.activity_type_id.name}"
            
            body_html = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #875A7B;">🔔 Recordatorio de Actividad</h2>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #343a40;">
                        📋 {activity.summary or activity.activity_type_id.name}
                    </h3>
                    
                    <p><strong>📅 Fecha:</strong> {activity.date_deadline.strftime('%d/%m/%Y')}</p>
                    <p><strong>🕐 Hora:</strong> {activity.deadline_time:02.0f}:00 hs</p>
                    <p><strong>📄 Documento:</strong> {activity._get_resource_name()}</p>
                    <p><strong>👤 Asignado a:</strong> {activity.user_id.name}</p>
                    
                    {f"<p><strong>📝 Notas:</strong><br/>{activity.note}</p>" if activity.note else ""}
                </div>
                
                <p style="color: #6c757d; font-size: 12px;">
                    Este es un recordatorio automático generado por el sistema Biagioli Group.
                </p>
            </div>
            """
            
            # Crear y enviar email
            mail_values = {
                'subject': subject,
                'body_html': body_html,
                'email_to': activity.user_id.email,
                'email_from': self.env.user.email or 'noreply@biagioli.com',
                'auto_delete': True,
            }
            
            mail = self.env['mail.mail'].create(mail_values)
            mail.send()
            
        except Exception as e:
            _logger.error(f"Error enviando email: {e}")
    
    def action_test_notification(self):
        """Método para probar notificaciones manualmente"""
        self.ensure_one()
        _logger.info(f"🧪 BIAGIOLI: Probando notificación para actividad #{self.id}")
        
        try:
            self._send_notification(self)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('✅ Éxito'),
                    'message': _('Notificación de prueba enviada correctamente'),
                    'type': 'success',
                    'sticky': False,
                }
            }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('❌ Error'),
                    'message': f'Error enviando notificación: {e}',
                    'type': 'danger',
                    'sticky': True,
                }
            }