# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class ProjectTask(models.Model):
    """Extender project.task para agregar notificaciones"""
    _inherit = 'project.task'
    
    # Campos para notificaciones de tareas
    task_time = fields.Float(
        string='Hora de la Tarea',
        help='Hora específica para la tarea (formato 24h, ej: 14.5 = 14:30)',
        default=9.0
    )
    
    reminder_time = fields.Selection([
        ('5', '5 minutos antes'),
        ('15', '15 minutos antes'),
        ('30', '30 minutos antes'),
        ('60', '1 hora antes'),
        ('120', '2 horas antes'),
        ('240', '4 horas antes'),
        ('480', '8 horas antes'),
        ('1440', '1 día antes'),
    ], string='Recordatorio', default='60', help='Cuándo enviar la notificación')
    
    notification_sent = fields.Boolean(
        string='Notificación Enviada',
        default=False,
        help='Indica si ya se envió la notificación de vencimiento'
    )
    
    enable_notifications = fields.Boolean(
        string='Habilitar Notificaciones',
        default=True,
        help='Activar notificaciones automáticas para esta tarea'
    )
    
    # Campo computado para mostrar fecha y hora completa
    full_deadline_display = fields.Char(
        string='Vencimiento Completo',
        compute='_compute_full_deadline_display',
        help='Muestra fecha y hora de vencimiento'
    )
    
    @api.depends('date_deadline', 'task_time')
    def _compute_full_deadline_display(self):
        """Mostrar fecha y hora de vencimiento"""
        for task in self:
            if task.date_deadline and task.task_time:
                hours = int(task.task_time)
                minutes = int((task.task_time - hours) * 60)
                task.full_deadline_display = f"{task.date_deadline.strftime('%d/%m/%Y')} a las {hours:02d}:{minutes:02d}"
            elif task.date_deadline:
                task.full_deadline_display = task.date_deadline.strftime('%d/%m/%Y')
            else:
                task.full_deadline_display = "Sin fecha límite"
    
    @api.model
    def _send_task_notifications(self):
        """Método ejecutado por cron para enviar notificaciones de tareas"""
        _logger.info("🔔 BIAGIOLI: Iniciando envío de notificaciones de tareas")
        
        # Buscar tareas que necesitan notificación
        tasks_to_notify = self._get_tasks_for_notification()
        
        if not tasks_to_notify:
            _logger.info("🔔 BIAGIOLI: No hay tareas para notificar")
            return
            
        _logger.info(f"🔔 BIAGIOLI: Encontradas {len(tasks_to_notify)} tareas para notificar")
        
        # Enviar notificaciones
        for task in tasks_to_notify:
            try:
                self._send_task_notification(task)
                task.notification_sent = True
                _logger.info(f"✅ BIAGIOLI: Notificación enviada para tarea #{task.id}")
            except Exception as e:
                _logger.error(f"❌ BIAGIOLI: Error enviando notificación para tarea #{task.id}: {e}")
    
    def _get_tasks_for_notification(self):
        """Obtener tareas que necesitan notificación"""
        now = datetime.now()
        
        # Buscar tareas activas con notificaciones habilitadas
        domain = [
            ('date_deadline', '>=', now.date()),     # Solo futuras o de hoy
            ('task_time', '!=', False),              # Que tengan hora específica
            ('enable_notifications', '=', True),     # Notificaciones habilitadas
            ('notification_sent', '=', False),       # Que no se haya enviado notificación
            ('user_ids', '!=', False),              # Que tengan usuarios asignados
            ('stage_id.fold', '=', False),          # Que no estén en etapa cerrada
        ]
        
        tasks = self.search(domain)
        tasks_to_notify = []
        
        for task in tasks:
            if task._should_send_notification(now):
                tasks_to_notify.append(task)
        
        return tasks_to_notify
    
    def _should_send_notification(self, current_time):
        """Verificar si es momento de enviar notificación"""
        if not self.task_time or not self.reminder_time or not self.date_deadline:
            return False
            
        # Convertir hora de tarea a datetime
        hours = int(self.task_time)
        minutes = int((self.task_time - hours) * 60)
        
        task_datetime = datetime.combine(
            self.date_deadline,
            datetime.min.time().replace(hour=hours, minute=minutes)
        )
        
        # Calcular momento de notificación
        reminder_minutes = int(self.reminder_time)
        notification_time = task_datetime - timedelta(minutes=reminder_minutes)
        
        # Verificar si es momento de notificar (con margen de 5 minutos)
        time_diff = abs((current_time - notification_time).total_seconds())
        return time_diff <= 300  # 5 minutos de margen
    
    def _send_task_notification(self, task):
        """Enviar notificación de vencimiento de tarea"""
        
        # 1. Notificación interna de Odoo
        self._send_internal_task_notification(task)
        
        # 2. Email (opcional) - enviar a todos los usuarios asignados
        for user in task.user_ids:
            if user.email:
                self._send_email_task_notification(task, user)
    
    def _send_internal_task_notification(self, task):
        """Enviar notificación interna de Odoo para tarea"""
        try:
            # Notificar a todos los usuarios asignados
            for user in task.user_ids:
                self.env['bus.bus']._sendone(
                    (self._cr.dbname, 'res.partner', user.partner_id.id),
                    'simple_notification',
                    {
                        'title': _('🔔 Tarea próxima a vencer'),
                        'message': f"📋 {task.name}\n"
                                  f"🕐 Vence a las {task.task_time:02.0f}:00 hs\n"
                                  f"📂 Proyecto: {task.project_id.name if task.project_id else 'Sin proyecto'}",
                        'type': 'warning',
                        'sticky': True,
                    }
                )
            
            # También crear mensaje en la tarea
            task.message_post(
                body=f"""
                <div class="alert alert-warning">
                    <h4>🔔 Recordatorio de Tarea</h4>
                    <p><strong>{task.name}</strong></p>
                    <p>📅 Vence hoy a las <strong>{task.task_time:02.0f}:00 hs</strong></p>
                    <p>👥 Asignado a: {', '.join(task.user_ids.mapped('name'))}</p>
                    <p>📂 Proyecto: {task.project_id.name if task.project_id else 'Sin proyecto'}</p>
                </div>
                """,
                message_type='notification',
                subtype_xmlid='mail.mt_note',
            )
        except Exception as e:
            _logger.error(f"Error enviando notificación interna: {e}")
    
    def _send_email_task_notification(self, task, user):
        """Enviar email de notificación de tarea"""
        try:
            # Preparar valores del email
            subject = f"🔔 Recordatorio: {task.name}"
            
            body_html = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #875A7B;">🔔 Recordatorio de Tarea</h2>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #343a40;">
                        📋 {task.name}
                    </h3>
                    
                    <p><strong>📅 Fecha:</strong> {task.date_deadline.strftime('%d/%m/%Y')}</p>
                    <p><strong>🕐 Hora:</strong> {task.task_time:02.0f}:00 hs</p>
                    <p><strong>📂 Proyecto:</strong> {task.project_id.name if task.project_id else 'Sin proyecto'}</p>
                    <p><strong>👤 Asignado a:</strong> {user.name}</p>
                    
                    {f"<p><strong>📝 Descripción:</strong><br/>{task.description}</p>" if task.description else ""}
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{self.env['ir.config_parameter'].sudo().get_param('web.base.url')}/web#id={task.id}&model=project.task&view_type=form" 
                       style="background-color: #875A7B; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        📋 Ver Tarea
                    </a>
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
                'email_to': user.email,
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
        _logger.info(f"🧪 BIAGIOLI: Probando notificación para tarea #{self.id}")
        
        try:
            self._send_task_notification(self)
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
    
    def action_reset_notification(self):
        """Resetear notificación para volver a enviarla"""
        self.ensure_one()
        self.notification_sent = False
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('✅ Reseteo exitoso'),
                'message': _('La notificación se puede enviar nuevamente'),
                'type': 'info',
                'sticky': False,
            }
        }