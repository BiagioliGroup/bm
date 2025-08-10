# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class MotorcycleService(models.Model):
    _name = 'motorcycle.service'
    _description = 'Servicio de Motocicleta'
    _rec_name = 'name'

    name = fields.Char(
        string='Número de Servicio',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('motorcycle.service.sequence') or 'Nuevo'
    )
    motorcycle_ids = fields.Many2many(
        'motorcycle.motorcycle',
        'motorcycle_service_rel',  # misma tabla relacional
        'service_id', 'motorcycle_id',
        string='Motocicletas',
        required=True
    )
    description = fields.Text(string='Descripción')
    labor_description = fields.Text(string='Descripción del Trabajo')

    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        default=lambda self: self.env.company.currency_id
    )

    service_line_ids = fields.One2many(
        'motorcycle.service.line',
        'service_id',
        string='Líneas del Servicio'
    )

    total_parts_cost = fields.Monetary(
        string='Costo de Repuestos',
        currency_field='currency_id',
        compute='_compute_totals',
        store=True,
        default=0.0
    )
    total_services_cost = fields.Monetary(
        string='Costo de Mano de Obra',
        currency_field='currency_id',
        compute='_compute_totals',
        store=True,
        default=0.0
    )
    total_service_cost = fields.Monetary(
        string='Costo Total',
        currency_field='currency_id',
        compute='_compute_totals',
        store=True,
        default=0.0
    )

    step_ids = fields.One2many(
        'motorcycle.service.step',
        'service_id',
        string='Pasos del Servicio'
    )

    @api.depends('service_line_ids.subtotal', 'service_line_ids.product_id.type')
    def _compute_totals(self):
        for service in self:
            parts_total = 0.0
            services_total = 0.0
            for line in service.service_line_ids:
                if line.display_type == 'line' and line.product_id:
                    if line.product_id.type == 'consu':
                        parts_total += line.subtotal
                    elif line.product_id.type == 'service':
                        services_total += line.subtotal
            service.total_parts_cost = parts_total
            service.total_services_cost = services_total
            service.total_service_cost = parts_total + services_total

    def action_print_service_report(self):
        """Método para imprimir reporte del servicio"""
        self.ensure_one()
        # Placeholder para futuro reporte personalizado
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reporte de Servicio',
            'res_model': 'motorcycle.service',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_motorcycles(self):
        """Método para ver las motocicletas del servicio"""
        self.ensure_one()
        motorcycles = self.motorcycle_ids
        
        action = {
            'type': 'ir.actions.act_window',
            'name': _('Motocicletas del Servicio %s') % self.name,
            'res_model': 'motorcycle.motorcycle',
            'domain': [('id', 'in', motorcycles.ids)],
            'context': {},
        }
        
        if len(motorcycles) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': motorcycles.id,
            })
        else:
            action.update({
                'view_mode': 'kanban,list,form',
            })
            
        return action

    def action_view_service_lines(self):
        """Método para ver las líneas del servicio"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Líneas del Servicio %s') % self.name,
            'res_model': 'motorcycle.service.line',
            'view_mode': 'list,form',
            'domain': [('service_id', '=', self.id)],
            'context': {
                'default_service_id': self.id,
            },
        }