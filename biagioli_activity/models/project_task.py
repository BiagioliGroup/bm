# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProjectTask(models.Model):
    """Extiende project.task para agregar campos de recursos"""
    _inherit = 'project.task'
    
    # Campos para vincular con el recurso origen
    resource_ref = fields.Reference(
        string='Referencia del Recurso',
        selection='_get_resource_ref_selection',
        help='Referencia al registro origen'
    )
    
    resource_model = fields.Char(
        string='Modelo del Recurso',
        help='Nombre técnico del modelo origen'
    )
    
    resource_id = fields.Integer(
        string='ID del Recurso',
        help='ID del registro origen'
    )
    
    resource_name = fields.Char(
        string='Nombre del Recurso',
        help='Nombre visible del registro origen'
    )
    
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
    
    @api.model
    def _get_resource_ref_selection(self):
        """Obtener modelos disponibles para referencia"""
        # Obtener los modelos más comunes que tienen actividades
        common_models = [
            'sale.order',
            'purchase.order',
            'account.move',
            'crm.lead',
            'project.project',
            'res.partner',
            'product.product',
            'stock.picking',
        ]
        
        selections = []
        for model_name in common_models:
            if model_name in self.env:
                model = self.env['ir.model'].search([('model', '=', model_name)], limit=1)
                if model:
                    selections.append((model_name, model.name))
        
        return selections
    
    @api.depends('activity_id')
    def _compute_is_from_activity(self):
        """Calcular si la tarea viene de una actividad"""
        for task in self:
            task.is_from_activity = bool(task.activity_id)
    
    def action_view_source_record(self):
        """Acción para ver el registro origen"""
        self.ensure_one()
        
        if not self.resource_model or not self.resource_id:
            return False
        
        return {
            'type': 'ir.actions.act_window',
            'name': self.resource_name or 'Registro Origen',
            'res_model': self.resource_model,
            'res_id': self.resource_id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    @api.model
    def create(self, vals):
        """Override create para manejar resource_ref"""
        # Si tenemos resource_model y resource_id pero no resource_ref
        if vals.get('resource_model') and vals.get('resource_id') and not vals.get('resource_ref'):
            vals['resource_ref'] = f"{vals['resource_model']},{vals['resource_id']}"
        
        # Si tenemos resource_ref pero no los campos individuales
        elif vals.get('resource_ref') and not vals.get('resource_model'):
            ref = vals['resource_ref']
            if isinstance(ref, str) and ',' in ref:
                model, res_id = ref.split(',')
                vals['resource_model'] = model
                vals['resource_id'] = int(res_id)
        
        return super(ProjectTask, self).create(vals)