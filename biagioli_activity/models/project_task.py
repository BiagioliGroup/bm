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
    
    @api.depends('activity_id')
    def _compute_is_from_activity(self):
        """Calcular si la tarea viene de una actividad"""
        for task in self:
            task.is_from_activity = bool(task.activity_id)
    
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