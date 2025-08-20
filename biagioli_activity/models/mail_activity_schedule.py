# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
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
        # Llamar al método padre primero
        result = super().action_schedule_activities()
        
        # Si hay proyecto seleccionado, agregarlo a las actividades creadas
        if self.project_id:
            try:
                # Buscar las actividades recién creadas
                domain = [
                    ('res_model', '=', self.res_model),
                    ('res_id', 'in', self.res_ids),
                    ('activity_type_id', '=', self.activity_type_id.id),
                    ('user_id', '=', self.user_id.id),
                    ('date_deadline', '=', self.date_deadline),
                    ('project_id', '=', False),  # Solo las que no tienen proyecto aún
                ]
                
                recent_activities = self.env['mail.activity'].search(
                    domain, 
                    order='create_date desc'
                )
                
                # Agregar proyecto a las actividades
                if recent_activities:
                    recent_activities.write({'project_id': self.project_id.id})
                    _logger.info(f"✅ Proyecto {self.project_id.name} asignado a {len(recent_activities)} actividades")
                    
                    # Crear tareas para actividades con proyecto
                    for activity in recent_activities:
                        if not activity.linked_task_id:
                            activity._create_project_task()
                            
            except Exception as e:
                _logger.error(f"❌ Error asignando proyecto a actividades: {e}")
        
        return result
    
    def action_schedule_activities_and_close(self):
        """Programar actividades y cerrar wizard"""
        self.action_schedule_activities()
        return {'type': 'ir.actions.act_window_close'}