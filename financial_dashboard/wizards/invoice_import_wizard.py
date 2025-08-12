# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta


class InvoiceImportWizard(models.TransientModel):
    _name = 'invoice.import.wizard'
    _description = 'Wizard para Importar Facturas al Cashflow'

    # Filtros de selección
    company_id = fields.Many2one('res.company', string='Compañía', 
                                default=lambda self: self.env.company, required=True)
    
    # Rango de fechas
    date_from = fields.Date(string='Fecha Desde', 
                           default=lambda self: fields.Date.today(),
                           required=True)
    date_to = fields.Date(string='Fecha Hasta', 
                         default=lambda self: fields.Date.today() + timedelta(days=90),
                         required=True)
    
    # Tipos de facturas a importar
    import_supplier_invoices = fields.Boolean(string='Facturas de Proveedores', default=True)
    import_customer_invoices = fields.Boolean(string='Facturas de Clientes', default=True)
    
    # Estados de pago
    import_not_paid = fields.Boolean(string='No Pagadas', default=True)
    import_partial = fields.Boolean(string='Parcialmente Pagadas', default=True)
    import_in_payment = fields.Boolean(string='En Proceso de Pago', default=False)
    
    # Filtros adicionales
    partner_ids = fields.Many2many('res.partner', string='Contactos Específicos',
                                  help="Dejar vacío para incluir todos")
    
    amount_min = fields.Monetary(string='Monto Mínimo', default=0)
    amount_max = fields.Monetary(string='Monto Máximo', default=0)
    
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    
    # Configuración de importación
    overwrite_existing = fields.Boolean(string='Sobrescribir Existentes', default=True,
                                       help="Actualizar proyecciones existentes para las mismas facturas")
    
    default_fiscal_type = fields.Selection([
        ('white', 'En Blanco'),
        ('black', 'En Negro')
    ], string='Tipo Fiscal por Defecto', default='white')
    
    # Campos de información
    preview_count = fields.Integer(string='Facturas Encontradas', compute='_compute_preview_count')
    preview_supplier_count = fields.Integer(string='Facturas de Proveedores', compute='_compute_preview_count')
    preview_customer_count = fields.Integer(string='Facturas de Clientes', compute='_compute_preview_count')
    preview_amount_total = fields.Monetary(string='Monto Total', compute='_compute_preview_count')
    
    # Resultados de la importación
    import_executed = fields.Boolean(string='Importación Ejecutada', default=False)
    import_result_ids = fields.Many2many('cashflow.projection', string='Proyecciones Creadas/Actualizadas')
    import_summary = fields.Text(string='Resumen de Importación')

    @api.depends('date_from', 'date_to', 'import_supplier_invoices', 'import_customer_invoices', 
                 'import_not_paid', 'import_partial', 'import_in_payment', 'partner_ids',
                 'amount_min', 'amount_max', 'company_id')
    def _compute_preview_count(self):
        for wizard in self:
            domain = wizard._get_invoice_domain()
            invoices = self.env['account.move'].search(domain)
            
            wizard.preview_count = len(invoices)
            wizard.preview_supplier_count = len(invoices.filtered(
                lambda x: x.move_type in ['in_invoice', 'in_receipt']
            ))
            wizard.preview_customer_count = len(invoices.filtered(
                lambda x: x.move_type in ['out_invoice', 'out_receipt']
            ))
            wizard.preview_amount_total = sum(invoices.mapped('amount_residual'))

    def _get_invoice_domain(self):
        """Construir dominio para buscar facturas según filtros"""
        domain = [
            ('company_id', '=', self.company_id.id),
            ('state', '=', 'posted'),
            ('amount_residual', '>', 0)
        ]
        
        # Fechas - usar fecha de vencimiento o fecha de factura
        if self.date_from:
            domain.append('|')
            domain.append(('invoice_date_due', '>=', self.date_from))
            domain.append('&')
            domain.append(('invoice_date_due', '=', False))
            domain.append(('invoice_date', '>=', self.date_from))
            
        if self.date_to:
            domain.append('|')
            domain.append(('invoice_date_due', '<=', self.date_to))
            domain.append('&')
            domain.append(('invoice_date_due', '=', False))
            domain.append(('invoice_date', '<=', self.date_to))
        
        # Tipos de facturas
        move_types = []
        if self.import_supplier_invoices:
            move_types.extend(['in_invoice', 'in_receipt'])
        if self.import_customer_invoices:
            move_types.extend(['out_invoice', 'out_receipt'])
        
        if move_types:
            domain.append(('move_type', 'in', move_types))
        
        # Estados de pago
        payment_states = []
        if self.import_not_paid:
            payment_states.append('not_paid')
        if self.import_partial:
            payment_states.append('partial')
        if self.import_in_payment:
            payment_states.append('in_payment')
        
        if payment_states:
            domain.append(('payment_state', 'in', payment_states))
        
        # Contactos específicos
        if self.partner_ids:
            domain.append(('partner_id', 'in', self.partner_ids.ids))
        
        # Montos
        if self.amount_min > 0:
            domain.append(('amount_residual', '>=', self.amount_min))
        if self.amount_max > 0:
            domain.append(('amount_residual', '<=', self.amount_max))
        
        return domain

    def action_preview_invoices(self):
        """Vista previa de facturas que serían importadas"""
        self.ensure_one()
        domain = self._get_invoice_domain()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Vista Previa - Facturas a Importar'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': domain,
            'context': {
                'create': False,
                'edit': False
            },
            'target': 'new'
        }

    def action_import_invoices(self):
        """Ejecutar importación de facturas al cashflow"""
        self.ensure_one()
        
        # Validaciones
        if not (self.import_supplier_invoices or self.import_customer_invoices):
            raise UserError(_('Debe seleccionar al menos un tipo de factura para importar'))
        
        if not (self.import_not_paid or self.import_partial or self.import_in_payment):
            raise UserError(_('Debe seleccionar al menos un estado de pago'))
        
        if self.date_from > self.date_to:
            raise UserError(_('La fecha desde no puede ser mayor a la fecha hasta'))
        
        # Obtener facturas a importar
        domain = self._get_invoice_domain()
        invoices = self.env['account.move'].search(domain)
        
        if not invoices:
            raise UserError(_('No se encontraron facturas con los criterios seleccionados'))
        
        # Procesar importación
        created_projections = []
        updated_projections = []
        skipped_invoices = []
        
        for invoice in invoices:
            try:
                result = self._create_or_update_projection(invoice)
                if result['action'] == 'created':
                    created_projections.append(result['projection_id'])
                elif result['action'] == 'updated':
                    updated_projections.append(result['projection_id'])
                else:
                    skipped_invoices.append(invoice.id)
            except Exception as e:
                skipped_invoices.append(invoice.id)
                continue
        
        # Actualizar wizard con resultados
        all_projection_ids = created_projections + updated_projections
        self.write({
            'import_executed': True,
            'import_result_ids': [(6, 0, all_projection_ids)],
            'import_summary': self._generate_import_summary(
                len(created_projections), 
                len(updated_projections), 
                len(skipped_invoices),
                len(invoices)
            )
        })
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Resultado de Importación'),
            'res_model': 'invoice.import.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new'
        }

    def _create_or_update_projection(self, invoice):
        """Crear o actualizar proyección para una factura específica"""
        # Determinar tipo y monto
        if invoice.move_type in ['in_invoice', 'in_receipt']:
            projection_type = 'egreso'
            source_type = 'supplier_invoice'
            amount = -invoice.amount_residual
        else:  # out_invoice, out_receipt
            projection_type = 'ingreso'
            source_type = 'customer_invoice'
            amount = invoice.amount_residual
        
        # Buscar proyección existente
        existing = self.env['cashflow.projection'].search([
            ('account_move_id', '=', invoice.id),
            ('source_type', '=', source_type)
        ])
        
        projection_vals = {
            'name': f"[{invoice.move_type.replace('_', ' ').title()}] {invoice.name}",
            'partner_id': invoice.partner_id.id,
            'date': invoice.invoice_date_due or invoice.invoice_date or invoice.date,
            'type': projection_type,
            'amount': amount,
            'source_type': source_type,
            'account_move_id': invoice.id,
            'payment_state': invoice.payment_state,
            'amount_residual': invoice.amount_residual,
            'invoice_date_due': invoice.invoice_date_due,
            'state': 'confirmed',
            'company_id': invoice.company_id.id,
            'fiscal_type': self.default_fiscal_type,
            'source_reference': invoice.ref or invoice.name,
            'notes': f"Importado desde factura {invoice.name} el {fields.Datetime.now().strftime('%d/%m/%Y %H:%M')}"
        }
        
        if existing:
            if self.overwrite_existing:
                existing.write(projection_vals)
                return {'action': 'updated', 'projection_id': existing.id}
            else:
                return {'action': 'skipped', 'projection_id': existing.id}
        else:
            projection = self.env['cashflow.projection'].create(projection_vals)
            return {'action': 'created', 'projection_id': projection.id}

    def _generate_import_summary(self, created_count, updated_count, skipped_count, total_count):
        """Generar resumen textual de la importación"""
        summary = []
        summary.append(f"=== RESUMEN DE IMPORTACIÓN ===")
        summary.append(f"Total de facturas procesadas: {total_count}")
        summary.append(f"Proyecciones creadas: {created_count}")
        summary.append(f"Proyecciones actualizadas: {updated_count}")
        summary.append(f"Facturas omitidas: {skipped_count}")
        summary.append("")
        
        if created_count > 0:
            summary.append("✓ Se crearon nuevas proyecciones de cashflow")
        if updated_count > 0:
            summary.append("✓ Se actualizaron proyecciones existentes")
        if skipped_count > 0:
            summary.append("⚠ Algunas facturas fueron omitidas (posibles errores o duplicados)")
        
        summary.append("")
        summary.append("Las proyecciones creadas están disponibles en:")
        summary.append("Dashboard Financiero > Cashflow > Proyección de Cashflow")
        
        return "\n".join(summary)

    def action_view_created_projections(self):
        """Ver proyecciones creadas/actualizadas"""
        self.ensure_one()
        
        if not self.import_result_ids:
            raise UserError(_('No hay proyecciones para mostrar'))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Proyecciones Importadas'),
            'res_model': 'cashflow.projection',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.import_result_ids.ids)],
            'context': {
                'create': False,
                'search_default_group_by_partner': 1
            }
        }

    def action_reset_wizard(self):
        """Resetear wizard para nueva importación"""
        self.write({
            'import_executed': False,
            'import_result_ids': [(5, 0, 0)],
            'import_summary': False
        })
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Importar Facturas al Cashflow'),
            'res_model': 'invoice.import.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new'
        }

    # ====================================================================
    # MÉTODOS AUXILIARES Y AUTOMÁTICOS
    # ====================================================================

    @api.model
    def auto_import_invoices(self, days_ahead=90):
        """Método para importación automática (cron job)"""
        date_from = fields.Date.today()
        date_to = fields.Date.today() + timedelta(days=days_ahead)
        
        # Crear wizard temporal para cada compañía
        companies = self.env['res.company'].search([])
        total_created = 0
        
        for company in companies:
            wizard = self.create({
                'company_id': company.id,
                'date_from': date_from,
                'date_to': date_to,
                'import_supplier_invoices': True,
                'import_customer_invoices': True,
                'import_not_paid': True,
                'import_partial': True,
                'default_fiscal_type': 'white',
                'overwrite_existing': True
            })
            
            try:
                # Ejecutar importación automática
                domain = wizard._get_invoice_domain()
                invoices = self.env['account.move'].search(domain)
                
                for invoice in invoices:
                    result = wizard._create_or_update_projection(invoice)
                    if result['action'] in ['created', 'updated']:
                        total_created += 1
                        
            except Exception as e:
                # Log error pero continúa con siguiente compañía
                import logging
                _logger = logging.getLogger(__name__)
                _logger.error(f"Error en auto_import_invoices para compañía {company.name}: {str(e)}")
            finally:
                # Limpiar wizard temporal
                wizard.unlink()
        
        return total_created

    @api.onchange('date_from', 'date_to')
    def _onchange_dates(self):
        """Validar fechas al cambiar"""
        if self.date_from and self.date_to and self.date_from > self.date_to:
            return {
                'warning': {
                    'title': _('Fechas Inválidas'),
                    'message': _('La fecha desde no puede ser mayor a la fecha hasta')
                }
            }

    @api.onchange('amount_min', 'amount_max')
    def _onchange_amounts(self):
        """Validar montos al cambiar"""
        if self.amount_min < 0 or self.amount_max < 0:
            return {
                'warning': {
                    'title': _('Montos Inválidos'),
                    'message': _('Los montos no pueden ser negativos')
                }
            }
        
        if self.amount_max > 0 and self.amount_min > self.amount_max:
            return {
                'warning': {
                    'title': _('Montos Inválidos'),
                    'message': _('El monto mínimo no puede ser mayor al monto máximo')
                }
            }