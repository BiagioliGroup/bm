# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProjectTask(models.Model):
    """Extiende project.task para agregar vínculo con actividades"""
    _inherit = 'project.task'
    
    # Campo para vincular con la actividad origen
    activity_id = fields.Many2one(
        'mail.activity',
        string='Actividad Origen',
        help='Actividad que creó esta tarea'
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