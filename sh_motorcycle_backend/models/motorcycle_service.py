# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.osv import expression  # ← ESTA LÍNEA FALTABA


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
        'motorcycle_service_rel',
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
    
    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        """
        Búsqueda inteligente que funciona con palabras parciales
        Ejemplo: "amort tras ktm 300 2022" encuentra servicios con esas palabras
        """
        if args is None:
            args = []
        
        if name and operator in ('ilike', '=ilike'):
            # Dividir en palabras (mínimo 2 caracteres)
            words = [word.strip() for word in name.split() if len(word.strip()) >= 2]
            
            if words:
                # Crear dominio para cada palabra
                word_domains = []
                
                for word in words:
                    # Intentar como año si es número
                    try:
                        year_val = int(word)
                        if year_val < 1900 or year_val > 2030:
                            year_val = 0
                    except:
                        year_val = 0
                    
                    # Buscar la palabra en múltiples campos
                    word_domain = [
                        '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|',
                        ('name', 'ilike', word),
                        ('description', 'ilike', word),
                        ('labor_description', 'ilike', word),
                        ('motorcycle_ids.name', 'ilike', word),
                        ('motorcycle_ids.make_id.name', 'ilike', word),
                        ('motorcycle_ids.mmodel_id.name', 'ilike', word),
                        ('motorcycle_ids.type_id.name', 'ilike', word),
                        ('service_line_ids.product_id.name', 'ilike', word),
                        ('service_line_ids.name', 'ilike', word),
                        ('step_ids.name', 'ilike', word),
                        ('step_ids.note', 'ilike', word),
                        ('motorcycle_ids.year', '=', year_val) if year_val > 0 else ('name', 'ilike', '___NEVER_MATCH___'),
                    ]
                    word_domains.append(word_domain)
                
                # Combinar: TODAS las palabras deben encontrarse
                if len(word_domains) == 1:
                    search_domain = word_domains[0]
                else:
                    search_domain = []
                    for i, domain in enumerate(word_domains):
                        if i > 0:
                            search_domain.append('&')
                        search_domain.extend(domain)
                
                # Combinar con args
                final_domain = expression.AND([args, search_domain])
                
                # Buscar
                try:
                    service_ids = self._search(final_domain, limit=limit, access_rights_uid=name_get_uid)
                    return self.browse(service_ids).name_get()
                except:
                    # Si falla, usar búsqueda simple
                    pass
        
        # Búsqueda normal como fallback
        return super()._name_search(name=name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid)

    def _try_parse_int(self, value):
        """Intenta convertir un string a entero, retorna 0 si falla"""
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0


    

    def name_get(self):
        """Mostrar información más descriptiva"""
        result = []
        for record in self:
            # Obtener nombres de hasta 2 motocicletas
            motorcycle_names = []
            for moto in record.motorcycle_ids[:2]:
                motorcycle_names.append(f"{moto.make_id.name} {moto.mmodel_id.name} {moto.year}")
            
            if len(record.motorcycle_ids) > 2:
                motorcycle_names.append(f"... +{len(record.motorcycle_ids) - 2} más")
            
            moto_str = " | ".join(motorcycle_names) if motorcycle_names else "Sin motocicletas"
            
            if record.description:
                desc = record.description[:30] + "..." if len(record.description) > 30 else record.description
                name = f"{record.name} - {desc} ({moto_str})"
            else:
                name = f"{record.name} ({moto_str})"
            
            result.append((record.id, name))
        return result


    @api.depends('description', 'labor_description')
    def _compute_display_name(self):
        for record in self:
            if record.description and record.labor_description:
                record.display_name = f"{record.description} [{record.labor_description}]"
            elif record.description:
                record.display_name = record.description
            elif record.labor_description:
                record.display_name = f"[{record.labor_description}]"
            else:
                record.display_name = record.name or "Nuevo Servicio"

    @api.depends('motorcycle_ids')
    def _compute_motorcycles_display(self):
        for record in self:
            if record.motorcycle_ids:
                moto_names = ', '.join(record.motorcycle_ids.mapped('name'))
                # Truncar a 100 caracteres
                if len(moto_names) > 100:
                    record.motorcycles_display = moto_names[:97] + "..."
                else:
                    record.motorcycles_display = moto_names
            else:
                record.motorcycles_display = ""

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
            'name': 'Motocicletas del Servicio %s' % self.name,
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
            'name': 'Líneas del Servicio %s' % self.name,
            'res_model': 'motorcycle.service.line',
            'view_mode': 'list,form',
            'domain': [('service_id', '=', self.id)],
            'context': {
                'default_service_id': self.id,
            },
        }

    def action_open_workflow_designer(self):
        """Abrir el diseñador de workflow en ventana separada"""
        self.ensure_one()
        window_name = self.description or self.name
        return {
            'type': 'ir.actions.act_window',
            'name': 'Workflow: %s' % window_name,
            'res_model': 'motorcycle.service',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('sh_motorcycle_backend.view_motorcycle_service_workflow_designer').id,
            'target': 'new',
            'context': {
                'default_service_id': self.id,
                'workflow_mode': True,
            },
            'flags': {
                'mode': 'readonly',
            },
            # Hacer la ventana más ancha
            'dialog_size': 'large',
        }

    def action_save_workflow(self):
        """Guardar el workflow actual"""
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Workflow Guardado',
                'message': 'El workflow ha sido guardado correctamente.',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_refresh_workflow(self):
        """Refrescar la vista del workflow"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Diseñador de Workflow - %s' % self.name,
            'res_model': 'motorcycle.service',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('sh_motorcycle_backend.view_motorcycle_service_workflow_designer').id,
            'target': 'new',
            'context': {
                'default_service_id': self.id,
                'workflow_mode': True,
            },
        }

    def create_workflow_template(self):
        """Crear plantilla básica de workflow"""
        self.ensure_one()
        
        # Eliminar pasos existentes si los hay
        self.step_ids.unlink()
        
        # Datos de la plantilla
        steps_data = [
            {
                'service_id': self.id,
                'name': 'Inicio del Servicio',
                'step_type': 'start',
                'sequence': 10,
                'position_x': 50,
                'position_y': 50,
                'note': 'Punto de inicio del proceso de servicio técnico'
            },
            {
                'service_id': self.id,
                'name': 'Inspección Visual General',
                'step_type': 'action',
                'sequence': 20,
                'position_x': 300,
                'position_y': 50,
                'note': 'Revisar estado general de la motocicleta, carrocería, luces, etc.'
            },
            {
                'service_id': self.id,
                'name': 'Revisión del Motor',
                'step_type': 'action',
                'sequence': 30,
                'position_x': 550,
                'position_y': 50,
                'note': 'Verificar niveles de aceite, refrigerante, filtros'
            },
            {
                'service_id': self.id,
                'name': '¿Requiere Cambio de Aceite?',
                'step_type': 'decision',
                'sequence': 40,
                'position_x': 300,
                'position_y': 200,
                'decision_question': '¿El aceite está sucio o ha cumplido su ciclo de mantenimiento?',
                'note': 'Evaluar color, viscosidad y kilometraje'
            },
            {
                'service_id': self.id,
                'name': 'Cambiar Aceite y Filtro',
                'step_type': 'action',
                'sequence': 50,
                'position_x': 50,
                'position_y': 350,
                'note': 'Drenar aceite usado, cambiar filtro, agregar aceite nuevo'
            },
            {
                'service_id': self.id,
                'name': 'Revisar Sistema de Frenos',
                'step_type': 'action',
                'sequence': 60,
                'position_x': 550,
                'position_y': 350,
                'note': 'Verificar pastillas, discos, nivel de líquido de frenos'
            },
            {
                'service_id': self.id,
                'name': '¿Requiere Repuestos?',
                'step_type': 'decision',
                'sequence': 70,
                'position_x': 300,
                'position_y': 500,
                'decision_question': '¿Se necesitan repuestos o componentes nuevos?',
                'note': 'Evaluar desgaste de componentes críticos'
            },
            {
                'service_id': self.id,
                'name': 'Cotizar y Solicitar Aprobación',
                'step_type': 'action',
                'sequence': 80,
                'position_x': 50,
                'position_y': 650,
                'note': 'Preparar cotización de repuestos y solicitar autorización del cliente'
            },
            {
                'service_id': self.id,
                'name': 'Prueba Final',
                'step_type': 'action',
                'sequence': 90,
                'position_x': 550,
                'position_y': 650,
                'note': 'Probar funcionamiento general, luces, frenos, motor'
            },
            {
                'service_id': self.id,
                'name': 'Entrega al Cliente',
                'step_type': 'end',
                'sequence': 100,
                'position_x': 300,
                'position_y': 800,
                'note': 'Explicar trabajo realizado y entregar motocicleta'
            }
        ]
        
        # Crear los pasos
        created_steps = []
        for step_data in steps_data:
            step = self.env['motorcycle.service.step'].create(step_data)
            created_steps.append(step)
        
        # Establecer conexiones del flujo
        if len(created_steps) >= 10:
            # Conexiones lineales principales
            created_steps[0].next_step_id = created_steps[1].id  # Inicio -> Inspección
            created_steps[1].next_step_id = created_steps[2].id  # Inspección -> Motor
            created_steps[2].next_step_id = created_steps[3].id  # Motor -> ¿Aceite?
            
            # Conexiones de decisión: ¿Aceite?
            created_steps[3].next_step_yes_id = created_steps[4].id  # SÍ -> Cambiar aceite
            created_steps[3].next_step_no_id = created_steps[5].id   # NO -> Revisar frenos
            
            # Flujo después del cambio de aceite
            created_steps[4].next_step_id = created_steps[5].id  # Aceite -> Frenos
            
            # Continuar con segunda decisión
            created_steps[5].next_step_id = created_steps[6].id  # Frenos -> ¿Repuestos?
            
            # Conexiones de decisión: ¿Repuestos?
            created_steps[6].next_step_yes_id = created_steps[7].id  # SÍ -> Cotizar
            created_steps[6].next_step_no_id = created_steps[8].id   # NO -> Prueba final
            
            # Flujo final
            created_steps[7].next_step_id = created_steps[8].id  # Cotizar -> Prueba
            created_steps[8].next_step_id = created_steps[9].id  # Prueba -> Entrega
        
        # Mostrar mensaje de confirmación
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Plantilla de Workflow Creada',
                'message': 'Se ha creado una plantilla básica con %d pasos. Puedes personalizarla según tus necesidades.' % len(created_steps),
                'type': 'success',
                'sticky': False,
            }
        }