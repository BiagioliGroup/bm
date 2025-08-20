# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)


class MailActivitySchedule(models.TransientModel):
    """Extiende mail.activity.schedule para agregar campo proyecto"""
    _inherit = 'mail.activity.schedule'
    
    # Campo proyecto para el wizard
    project_id = fields.Many2one(
        'project.project',
        string='Proyecto',
        help='Proyecto vinculado a esta actividad (opcional)'
    )
    
    # Campo de hora específica
    deadline_time = fields.Float(
        string='Hora de Vencimiento',
        help='Hora específica del vencimiento (formato 24h, ej: 14.5 = 14:30)',
        default=9.0  # 9:00 AM por defecto
    )
    
    # Campo de recordatorio
    reminder_time = fields.Selection([
        ('15', '15 minutos antes'),
        ('30', '30 minutos antes'),
        ('60', '1 hora antes'),
        ('120', '2 horas antes'),
        ('240', '4 horas antes'),
        ('480', '8 horas antes'),
        ('1440', '1 día antes'),
    ], string='Recordatorio', default='60', help='Cuándo enviar la notificación')
    
    def action_schedule_activities(self):
        """Override para pasar el proyecto_id a las actividades creadas"""
        _logger.info(f"🟪 BIAGIOLI SCHEDULE: Iniciando action_schedule_activities()")
        _logger.info(f"🟪 BIAGIOLI SCHEDULE: project_id seleccionado: {self.project_id}")
        
        # Llamar al método padre que crea las actividades
        result = super().action_schedule_activities()
        
        # Si hay proyecto seleccionado, agregarlo a las actividades recién creadas
        if self.project_id:
            try:
                _logger.info(f"🟪 BIAGIOLI SCHEDULE: Buscando actividades para asignar proyecto...")
                
                # Buscar las actividades recién creadas (últimos 2 minutos)
                from datetime import datetime, timedelta
                recent_time = fields.Datetime.now() - timedelta(minutes=2)
                
                # Asegurar que res_ids sea una lista
                res_ids = self.res_ids
                if isinstance(res_ids, str):
                    # Si es string, convertir a lista
                    import ast
                    res_ids = ast.literal_eval(res_ids)
                elif not isinstance(res_ids, list):
                    res_ids = [res_ids]
                
                domain = [
                    ('res_model', '=', self.res_model),
                    ('res_id', 'in', res_ids),
                    ('activity_type_id', '=', self.activity_type_id.id),
                    ('project_id', '=', False),  # Solo las que no tienen proyecto aún
                    ('create_date', '>=', recent_time)
                ]
                
                recent_activities = self.env['mail.activity'].search(
                    domain, 
                    order='create_date desc'
                )
                
                _logger.info(f"🟪 BIAGIOLI SCHEDULE: Encontradas {len(recent_activities)} actividades recientes")
                
                # Agregar proyecto a las actividades
                if recent_activities:
                    # Preparar valores incluyendo deadline_time y reminder_time
                    vals_to_update = {'project_id': self.project_id.id}
                    if hasattr(self, 'deadline_time') and self.deadline_time:
                        vals_to_update['deadline_time'] = self.deadline_time
                    if hasattr(self, 'reminder_time') and self.reminder_time:
                        vals_to_update['reminder_time'] = self.reminder_time
                    
                    recent_activities.write(vals_to_update)
                    _logger.info(f"✅ BIAGIOLI SCHEDULE: Proyecto, hora y recordatorio asignados a {len(recent_activities)} actividades")
                    
                    # Forzar la creación de tareas para estas actividades
                    for activity in recent_activities:
                        if not activity.linked_task_id:
                            _logger.info(f"🟪 BIAGIOLI SCHEDULE: Creando tarea para actividad #{activity.id}")
                            task = activity._create_project_task()
                            if task:
                                _logger.info(f"✅ BIAGIOLI SCHEDULE: Tarea #{task.id} creada!")
                else:
                    _logger.warning(f"⚠️ BIAGIOLI SCHEDULE: No se encontraron actividades recientes")
                    
            except Exception as e:
                _logger.error(f"❌ BIAGIOLI SCHEDULE: Error asignando proyecto: {e}")
                import traceback
                _logger.error(f"❌ BIAGIOLI SCHEDULE: Traceback: {traceback.format_exc()}")
        else:
            _logger.info(f"🟪 BIAGIOLI SCHEDULE: No hay proyecto seleccionado")
        
        return result
    
    def action_schedule_activities_and_close(self):
        """Programar actividades y cerrar wizard"""
        self.action_schedule_activities()
        return {'type': 'ir.actions.act_window_close'}