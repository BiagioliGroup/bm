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
                
                domain = [
                    ('res_model', '=', self.res_model),
                    ('res_id', 'in', self.res_ids),
                    ('activity_type_id', '=', self.activity_type_id.id),
                    ('project_id', '=', False),  # Solo las que no tienen proyecto aún
                    ('create_date', '>=', recent_time)
                ]
                
                recent_activities = self.env['mail.activity'].search(
                    domain, 
                    order='create_date desc'
                )
                
                _logger.info(f"🟪 BIAGIOLI SCHEDULE: Encontradas {len(recent_activities)} actividades recientes")
                
                # Simplemente asignar el proyecto - el create() de mail.activity se encarga del resto
                if recent_activities:
                    recent_activities.write({'project_id': self.project_id.id})
                    _logger.info(f"✅ BIAGIOLI SCHEDULE: Proyecto asignado a {len(recent_activities)} actividades")
                    
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