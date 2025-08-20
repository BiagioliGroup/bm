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
        # Guardar el proyecto_id antes de llamar al padre
        project_id = self.project_id.id if self.project_id else False
        
        # Llamar al método padre que crea las actividades
        result = super().action_schedule_activities()
        
        # Si hay proyecto seleccionado, agregarlo a las actividades recién creadas
        if project_id:
            try:
                # Buscar las actividades recién creadas (últimos 5 minutos)
                domain = [
                    ('res_model', '=', self.res_model),
                    ('res_id', 'in', self.res_ids),
                    ('activity_type_id', '=', self.activity_type_id.id),
                    ('user_id', '=', self.user_id.id),
                    ('date_deadline', '=', self.date_deadline),
                    ('project_id', '=', False),  # Solo las que no tienen proyecto aún
                    ('create_date', '>=', fields.Datetime.now() - timedelta(minutes=5))
                ]
                
                recent_activities = self.env['mail.activity'].search(
                    domain, 
                    order='create_date desc'
                )
                
                # Simplemente asignar el proyecto - el create() de mail.activity se encarga del resto
                if recent_activities:
                    recent_activities.write({'project_id': project_id})
                    _logger.info(f"✅ Proyecto asignado a {len(recent_activities)} actividades")
                    
            except Exception as e:
                _logger.error(f"❌ Error asignando proyecto a actividades: {e}")
        
        return result
    
    def action_schedule_activities_and_close(self):
        """Programar actividades y cerrar wizard"""
        self.action_schedule_activities()
        return {'type': 'ir.actions.act_window_close'}