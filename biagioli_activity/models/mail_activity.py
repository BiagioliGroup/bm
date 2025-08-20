# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class MailActivity(models.Model):
    """Extiende mail.activity para agregar integración con proyectos"""
    _inherit = 'mail.activity'
    
    # Campos adicionales
    project_id = fields.Many2one(
        'project.project',
        string='Proyecto',
        help='Proyecto vinculado a esta actividad'
    )
    
    linked_task_id = fields.Many2one(
        'project.task',
        string='Tarea Vinculada',
        readonly=True,
        help='Tarea creada desde esta actividad'
    )
    
    # Campo de hora específica (simplificado)
    deadline_time = fields.Float(
        string='Hora de Vencimiento',
        help='Hora específica del vencimiento (formato 24h, ej: 14.5 = 14:30)',
        default=9.0  # 9:00 AM por defecto
    )
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override para crear tareas cuando hay proyecto"""
        _logger.info("🟦 BIAGIOLI: Iniciando create() de mail.activity")
        _logger.info(f"🟦 BIAGIOLI: vals_list recibido: {vals_list}")
        
        # Primero crear las actividades
        activities = super().create(vals_list)
        _logger.info(f"🟦 BIAGIOLI: {len(activities)} actividades creadas")
        
        # Luego crear las tareas para las que tienen proyecto
        for i, activity in enumerate(activities):
            _logger.info(f"🟦 BIAGIOLI: Procesando actividad #{activity.id}")
            _logger.info(f"🟦 BIAGIOLI: - activity.project_id: {activity.project_id}")
            _logger.info(f"🟦 BIAGIOLI: - activity.linked_task_id: {activity.linked_task_id}")
            _logger.info(f"🟦 BIAGIOLI: - activity.summary: {activity.summary}")
            _logger.info(f"🟦 BIAGIOLI: - activity.res_model: {activity.res_model}")
            _logger.info(f"🟦 BIAGIOLI: - activity.res_id: {activity.res_id}")
            
            if activity.project_id and not activity.linked_task_id:
                _logger.info(f"🟢 BIAGIOLI: ¡Condiciones cumplidas! Creando tarea para actividad #{activity.id}")
                try:
                    task = activity._create_project_task()
                    if task:
                        _logger.info(f"✅ BIAGIOLI: Tarea #{task.id} creada para actividad #{activity.id}")
                    else:
                        _logger.warning(f"⚠️ BIAGIOLI: _create_project_task() retornó False para actividad #{activity.id}")
                except Exception as e:
                    _logger.error(f"❌ BIAGIOLI: Error creando tarea para actividad #{activity.id}: {e}")
                    import traceback
                    _logger.error(f"❌ BIAGIOLI: Traceback: {traceback.format_exc()}")
            else:
                if not activity.project_id:
                    _logger.info(f"🟡 BIAGIOLI: Actividad #{activity.id} sin proyecto - no se crea tarea")
                elif activity.linked_task_id:
                    _logger.info(f"🟡 BIAGIOLI: Actividad #{activity.id} ya tiene tarea vinculada")
                
        return activities
    
    def _create_project_task(self):
        """Crear tarea de proyecto desde la actividad"""
        self.ensure_one()
        _logger.info(f"🔵 BIAGIOLI: Iniciando _create_project_task() para actividad #{self.id}")
        
        if not self.project_id:
            _logger.warning(f"🔴 BIAGIOLI: No hay project_id en actividad #{self.id}")
            return False
            
        # Obtener información del recurso
        resource_name = self._get_resource_name()
        _logger.info(f"🔵 BIAGIOLI: resource_name obtenido: {resource_name}")
        
        # Preparar valores de la tarea - usar summary si existe, sino activity_type
        task_name = self.summary if self.summary else self.activity_type_id.name
        
        # Combinar fecha y hora para la fecha límite de la tarea
        task_deadline = self.date_deadline
        if self.deadline_time:
            from datetime import datetime, time
            import pytz
            
            hours = int(self.deadline_time)
            minutes = int((self.deadline_time - hours) * 60)
            
            # Crear datetime en zona horaria del usuario
            user_tz = pytz.timezone(self.env.user.tz or 'America/Argentina/Buenos_Aires')
            
            # Crear datetime naive
            naive_datetime = datetime.combine(
                self.date_deadline,
                time(hours, minutes)
            )
            
            # Convertir a zona horaria del usuario y luego a UTC para Odoo
            localized_dt = user_tz.localize(naive_datetime)
            task_deadline = localized_dt.astimezone(pytz.UTC).replace(tzinfo=None)
        
        task_vals = {
            'name': f"{task_name}: {resource_name}",
            'project_id': self.project_id.id,
            'user_ids': [(4, self.user_id.id)],
            'date_deadline': task_deadline,  # Ahora incluye la hora corregida
            'description': f"""
                <p><b>Actividad origen:</b> {self.activity_type_id.name}</p>
                <p><b>Resumen:</b> {self.summary or 'Sin resumen'}</p>
                <p><b>Recurso:</b> {resource_name}</p>
                <p><b>Fecha límite:</b> {self.date_deadline} a las {self.deadline_time:02.0f}:00</p>
                <p><b>Notas:</b></p>
                {self.note or '<p>Sin notas</p>'}
            """,
            'priority': '1',  # Normal
        }
        
        _logger.info(f"🔵 BIAGIOLI: task_vals preparados: {task_vals}")
        
        try:
            # Crear la tarea
            task = self.env['project.task'].sudo().create(task_vals)
            _logger.info(f"🔵 BIAGIOLI: Tarea creada con ID: {task.id}")
            
            # Vincular la tarea con la actividad
            self.sudo().write({'linked_task_id': task.id})
            _logger.info(f"🔵 BIAGIOLI: linked_task_id actualizado en actividad #{self.id}")
            
            # Agregar campo de tracking a la tarea
            task.sudo().write({'activity_id': self.id})
            _logger.info(f"🔵 BIAGIOLI: activity_id actualizado en tarea #{task.id}")
            
            _logger.info(f"✅ BIAGIOLI: Tarea #{task.id} '{task.name}' creada en proyecto '{self.project_id.name}'")
            
            # No postear mensaje automático en el chatter
            # La creación de la tarea es suficiente notificación
            
            return task
            
        except Exception as e:
            _logger.error(f"❌ BIAGIOLI: Error en creación de tarea: {e}")
            import traceback
            _logger.error(f"❌ BIAGIOLI: Traceback completo: {traceback.format_exc()}")
            return False
    
    def _get_resource_name(self):
        """Obtener el nombre del recurso"""
        self.ensure_one()
        _logger.info(f"🟠 BIAGIOLI: Obteniendo nombre del recurso para {self.res_model}#{self.res_id}")
        
        try:
            if self.res_model and self.res_id:
                record = self.env[self.res_model].browse(self.res_id)
                if record.exists():
                    # Intentar diferentes campos de nombre
                    for field in ['display_name', 'name', 'reference', 'number']:
                        if hasattr(record, field):
                            value = getattr(record, field)
                            if value:
                                _logger.info(f"🟠 BIAGIOLI: Nombre encontrado: {value}")
                                return str(value)
                return f"{self.res_model}#{self.res_id}"
            return "Sin recurso"
        except Exception as e:
            _logger.warning(f"🟠 BIAGIOLI: Error obteniendo nombre del recurso: {e}")
            return f"{self.res_model}#{self.res_id}"
    
    def action_done(self):
        """Marcar actividad como completada y actualizar tarea"""
        for activity in self:
            if activity.linked_task_id:
                try:
                    # Buscar etapa de completado en el proyecto
                    done_stage = self.env['project.task.type'].search([
                        ('fold', '=', True),
                        '|',
                        ('project_ids', '=', False),
                        ('project_ids', 'in', activity.project_id.id)
                    ], limit=1)
                    
                    if done_stage:
                        activity.linked_task_id.sudo().write({'stage_id': done_stage.id})
                        _logger.info(f"✅ BIAGIOLI: Tarea #{activity.linked_task_id.id} marcada como completada")
                except Exception as e:
                    _logger.warning(f"⚠️ BIAGIOLI: No se pudo actualizar tarea: {e}")
                    
        return super().action_done()
    
    def unlink(self):
        """Al eliminar actividad, informar sobre tareas vinculadas"""
        tasks = self.mapped('linked_task_id')
        if tasks:
            _logger.info(f"⚠️ BIAGIOLI: Se eliminarán actividades con tareas vinculadas: {tasks.ids}")
        return super().unlink()