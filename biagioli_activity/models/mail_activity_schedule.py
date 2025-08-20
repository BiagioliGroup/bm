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
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override para crear tareas cuando hay proyecto"""
        # Primero crear las actividades
        activities = super().create(vals_list)
        
        # Luego crear las tareas para las que tienen proyecto
        for activity in activities:
            if activity.project_id and not activity.linked_task_id:
                try:
                    task = activity._create_project_task()
                    if task:
                        _logger.info(f"✅ Tarea #{task.id} creada para actividad #{activity.id}")
                except Exception as e:
                    _logger.error(f"❌ Error creando tarea para actividad #{activity.id}: {e}")
                
        return activities
    
    def _create_project_task(self):
        """Crear tarea de proyecto desde la actividad"""
        self.ensure_one()
        
        if not self.project_id:
            return False
            
        # Obtener información del recurso
        resource_name = self._get_resource_name()
        
        # Preparar valores de la tarea
        task_vals = {
            'name': f"{self.activity_type_id.name}: {resource_name}",
            'project_id': self.project_id.id,
            'user_ids': [(4, self.user_id.id)],
            'date_deadline': self.date_deadline,
            'description': f"""
                <p><b>Actividad origen:</b> {self.activity_type_id.name}</p>
                <p><b>Resumen:</b> {self.summary or 'Sin resumen'}</p>
                <p><b>Recurso:</b> {resource_name}</p>
                <p><b>Notas:</b></p>
                {self.note or '<p>Sin notas</p>'}
            """,
            'priority': '1',  # Normal
        }
        
        # Crear la tarea
        task = self.env['project.task'].sudo().create(task_vals)
        
        # Vincular la tarea con la actividad
        self.sudo().write({'linked_task_id': task.id})
        
        # Agregar campo de tracking a la tarea
        task.sudo().write({'activity_id': self.id})
        
        _logger.info(f"Tarea #{task.id} '{task.name}' creada en proyecto '{self.project_id.name}'")
        
        # Mensaje en el chatter del recurso origen
        self._post_task_creation_message(task)
        
        return task
    
    def _get_resource_name(self):
        """Obtener el nombre del recurso"""
        self.ensure_one()
        try:
            if self.res_model and self.res_id:
                record = self.env[self.res_model].browse(self.res_id)
                if record.exists():
                    # Intentar diferentes campos de nombre
                    for field in ['display_name', 'name', 'reference', 'number']:
                        if hasattr(record, field):
                            value = getattr(record, field)
                            if value:
                                return str(value)
                return f"{self.res_model}#{self.res_id}"
            return "Sin recurso"
        except Exception as e:
            _logger.warning(f"Error obteniendo nombre del recurso: {e}")
            return f"{self.res_model}#{self.res_id}"
    
    def _post_task_creation_message(self, task):
        """Postear mensaje sobre la tarea creada"""
        try:
            if self.res_model and self.res_id:
                record = self.env[self.res_model].browse(self.res_id)
                if record.exists() and hasattr(record, 'message_post'):
                    record.message_post(
                        body=f"""
                        <div style="margin: 10px 0; padding: 10px; background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 4px;">
                            <i class="fa fa-check-circle text-success"/> 
                            <b>Tarea creada automáticamente:</b><br/>
                            <a href="#" data-oe-model="project.task" data-oe-id="{task.id}" style="font-weight: bold;">
                                <i class="fa fa-tasks"/> #{task.id} - {task.name}
                            </a><br/>
                            <b>Proyecto:</b> {self.project_id.name}<br/>
                            <b>Asignado a:</b> {self.user_id.name}<br/>
                            <b>Fecha límite:</b> {self.date_deadline}
                        </div>
                        """,
                        message_type='notification',
                        subtype_xmlid='mail.mt_note',
                    )
                    _logger.info(f"✅ Mensaje posteado en {self.res_model}#{self.res_id}")
        except Exception as e:
            _logger.warning(f"⚠️ No se pudo postear mensaje: {e}")
    
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
                        _logger.info(f"✅ Tarea #{activity.linked_task_id.id} marcada como completada")
                except Exception as e:
                    _logger.warning(f"⚠️ No se pudo actualizar tarea: {e}")
                    
        return super().action_done()
    
    def unlink(self):
        """Al eliminar actividad, informar sobre tareas vinculadas"""
        tasks = self.mapped('linked_task_id')
        if tasks:
            _logger.info(f"⚠️ Se eliminarán actividades con tareas vinculadas: {tasks.ids}")
        return super().unlink()