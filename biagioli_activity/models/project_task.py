# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class ProjectTask(models.Model):
    """Extiende project.task para agregar vínculo con actividades"""
    _inherit = 'project.task'
    
    # Campo para vincular con la actividad origen
    activity_id = fields.Many2one(
        'mail.activity',
        string='Actividad Origen',
        help='Actividad que creó esta tarea',
        ondelete='set null'
    )
    
    is_from_activity = fields.Boolean(
        string='Creada desde Actividad',
        compute='_compute_is_from_activity',
        store=True
    )
    
    # Campos relacionados para mostrar información del documento origen
    source_document_model = fields.Char(
        string='Modelo del Documento',
        related='activity_id.res_model',
        readonly=True
    )
    
    source_document_id = fields.Integer(
        string='ID del Documento',
        related='activity_id.res_id',
        readonly=True
    )
    
    source_document_name = fields.Char(
        string='Nombre del Documento',
        compute='_compute_source_document_name',
        store=False
    )
    
    @api.depends('activity_id')
    def _compute_is_from_activity(self):
        """Calcular si la tarea viene de una actividad"""
        for task in self:
            task.is_from_activity = bool(task.activity_id)
    
    @api.depends('activity_id', 'source_document_model', 'source_document_id')
    def _compute_source_document_name(self):
        """Obtener el nombre del documento origen"""
        for task in self:
            if task.activity_id and task.source_document_model and task.source_document_id:
                try:
                    record = self.env[task.source_document_model].browse(task.source_document_id)
                    if record.exists():
                        task.source_document_name = record.display_name
                    else:
                        task.source_document_name = f"{task.source_document_model}#{task.source_document_id}"
                except:
                    task.source_document_name = f"{task.source_document_model}#{task.source_document_id}"
            else:
                task.source_document_name = False
    
    def action_view_source_activity(self):
        """Ver la actividad origen"""
        self.ensure_one()
        if not self.activity_id:
            return False
            
        return {
            'type': 'ir.actions.act_window',
            'name': 'Actividad Origen',
            'res_model': 'mail.activity',
            'res_id': self.activity_id.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def action_view_source_document(self):
        """Ver el documento origen de la actividad"""
        self.ensure_one()
        if not self.activity_id or not self.activity_id.res_model or not self.activity_id.res_id:
            return False
            
        # Obtener el modelo y registro origen
        res_model = self.activity_id.res_model
        res_id = self.activity_id.res_id
        
        # Buscar el registro origen
        try:
            record = self.env[res_model].browse(res_id)
            if not record.exists():
                return False
                
            # Determinar el nombre para la ventana
            display_name = record.display_name if hasattr(record, 'display_name') else f"{res_model}#{res_id}"
            
            return {
                'type': 'ir.actions.act_window',
                'name': f'Documento Origen: {display_name}',
                'res_model': res_model,
                'res_id': res_id,
                'view_mode': 'form',
                'target': 'current',  # Abrir en la ventana principal
                'context': {'create': False},  # Solo lectura
            }
        except Exception as e:
            _logger.warning(f"Error abriendo documento origen: {e}")
            return False