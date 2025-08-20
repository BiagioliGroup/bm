# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProjectTodo(models.Model):
    """Modelo para To-Dos (tareas personales sin proyecto)"""
    _name = 'project.todo'
    _description = 'To-Do Personal'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, date_deadline, id desc'
    
    name = fields.Char(
        string='Título',
        required=True,
        tracking=True
    )
    
    description = fields.Html(
        string='Descripción',
        sanitize=True
    )
    
    user_ids = fields.Many2many(
        'res.users',
        string='Asignado a',
        default=lambda self: [self.env.user.id],
        tracking=True
    )
    
    state = fields.Selection([
        ('open', 'Abierto'),
        ('in_progress', 'En Progreso'),
        ('done', 'Completado'),
        ('cancelled', 'Cancelado'),
    ], string='Estado', default='open', tracking=True)
    
    priority = fields.Selection([
        ('low', 'Baja'),
        ('normal', 'Normal'),
        ('high', 'Alta'),
        ('urgent', 'Urgente'),
    ], string='Prioridad', default='normal', tracking=True)
    
    date_deadline = fields.Date(
        string='Fecha Límite',
        tracking=True
    )
    
    date_done = fields.Datetime(
        string='Fecha de Completado',
        readonly=True
    )
    
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
        help='Actividad que creó este to-do'
    )
    
    is_from_activity = fields.Boolean(
        string='Creado desde Actividad',
        compute='_compute_is_from_activity',
        store=True
    )
    
    color = fields.Integer(
        string='Índice de Color',
        default=0
    )
    
    # Campos computados
    is_overdue = fields.Boolean(
        string='Está Vencido',
        compute='_compute_is_overdue',
        search='_search_is_overdue'
    )
    
    days_until_deadline = fields.Integer(
        string='Días hasta el Vencimiento',
        compute='_compute_days_until_deadline'
    )
    
    @api.model
    def _get_resource_ref_selection(self):
        """Obtener modelos disponibles para referencia"""
        models = self.env['ir.model'].search([
            ('is_mail_activity', '=', True)
        ])
        return [(model.model, model.name) for model in models]
    
    @api.depends('activity_id')
    def _compute_is_from_activity(self):
        """Calcular si el to-do viene de una actividad"""
        for todo in self:
            todo.is_from_activity = bool(todo.activity_id)
    
    @api.depends('date_deadline', 'state')
    def _compute_is_overdue(self):
        """Calcular si está vencido"""
        today = fields.Date.today()
        for todo in self:
            todo.is_overdue = bool(
                todo.date_deadline and 
                todo.date_deadline < today and 
                todo.state not in ['done', 'cancelled']
            )
    
    def _search_is_overdue(self, operator, value):
        """Búsqueda para to-dos vencidos"""
        today = fields.Date.today()
        if operator == '=' and value:
            return [
                ('date_deadline', '<', today),
                ('state', 'not in', ['done', 'cancelled'])
            ]
        return []
    
    @api.depends('date_deadline')
    def _compute_days_until_deadline(self):
        """Calcular días hasta el vencimiento"""
        today = fields.Date.today()
        for todo in self:
            if todo.date_deadline:
                delta = todo.date_deadline - today
                todo.days_until_deadline = delta.days
            else:
                todo.days_until_deadline = 0
    
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
    
    def action_mark_done(self):
        """Marcar como completado"""
        self.write({
            'state': 'done',
            'date_done': fields.Datetime.now()
        })
    
    def action_mark_in_progress(self):
        """Marcar como en progreso"""
        self.write({'state': 'in_progress'})
    
    def action_reopen(self):
        """Reabrir to-do"""
        self.write({
            'state': 'open',
            'date_done': False
        })
    
    def action_cancel(self):
        """Cancelar to-do"""
        self.write({'state': 'cancelled'})
    
    @api.model
    def create(self, vals):
        """Override create para manejar resource_ref"""
        # Sincronizar campos de recurso
        if vals.get('resource_model') and vals.get('resource_id') and not vals.get('resource_ref'):
            vals['resource_ref'] = f"{vals['resource_model']},{vals['resource_id']}"
        elif vals.get('resource_ref') and not vals.get('resource_model'):
            ref = vals['resource_ref']
            if isinstance(ref, str) and ',' in ref:
                model, res_id = ref.split(',')
                vals['resource_model'] = model
                vals['resource_id'] = int(res_id)
        
        return super(ProjectTodo, self).create(vals)
    
    def write(self, vals):
        """Override write para mantener sincronizados los campos de recurso"""
        # Sincronizar resource_ref con campos individuales
        if vals.get('resource_model') and vals.get('resource_id'):
            vals['resource_ref'] = f"{vals['resource_model']},{vals['resource_id']}"
        elif vals.get('resource_ref'):
            ref = vals['resource_ref']
            if isinstance(ref, str) and ',' in ref:
                model, res_id = ref.split(',')
                vals['resource_model'] = model
                vals['resource_id'] = int(res_id)
        
        return super(ProjectTodo, self).write(vals)
    
    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        """Override para personalizar vistas según contexto"""
        res = super(ProjectTodo, self).get_view(view_id, view_type, **options)
        
        # Personalizar vista kanban para mostrar prioridades con colores
        if view_type == 'kanban':
            # Aquí podrías modificar la vista dinámicamente si es necesario
            pass
        
        return res