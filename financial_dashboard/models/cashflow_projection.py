# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class CashflowProjection(models.Model):
    _name = 'cashflow.projection'
    _description = 'Proyección de Cashflow Avanzado'
    _order = 'date desc, type, partner_id'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Información básica
    name = fields.Char(string='Concepto', required=True, tracking=True)
    partner_id = fields.Many2one('res.partner', string='Contacto', tracking=True)
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company, required=True)
    
    # Fechas y periodicidad
    date = fields.Date(string='Fecha', required=True, tracking=True)
    week = fields.Char(string='Semana', compute='_compute_period_fields', store=True)
    month = fields.Char(string='Mes', compute='_compute_period_fields', store=True)
    quarter = fields.Char(string='Trimestre', compute='_compute_period_fields', store=True)
    year = fields.Char(string='Año', compute='_compute_period_fields', store=True)
    
    # Tipo y clasificación fiscal
    type = fields.Selection([
        ('ingreso', 'Ingreso'),
        ('egreso', 'Egreso')
    ], string='Tipo', required=True, tracking=True)
    
    fiscal_type = fields.Selection([
        ('white', 'En Blanco'),
        ('black', 'En Negro')
    ], string='Clasificación Fiscal', default='white', required=True, tracking=True)
    
    # Categorización por diario/rubro
    journal_type = fields.Selection([
        ('fiscal', 'Fiscal'),
        ('nofiscal', 'No Fiscal'),
        ('cash', 'Efectivo'),
        ('bank', 'Banco'),
        ('credit', 'Crédito')
    ], string='Tipo de Diario', default='fiscal')
    
    # Montos
    amount = fields.Monetary(string='Importe', required=True, tracking=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True)
    
    # Estado y seguimiento
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('projected', 'Proyectado'),
        ('confirmed', 'Confirmado'),
        ('realized', 'Realizado'),
        ('cancelled', 'Cancelado')
    ], string='Estado', default='projected', tracking=True)
    
    # NUEVA FUNCIONALIDAD: Origen del movimiento (incluyendo facturas)
    source_type = fields.Selection([
        ('manual', 'Manual'),
        ('periodic', 'Gasto Periódico'),
        ('invoice', 'Factura'),
        ('payment', 'Pago'),
        ('budget', 'Presupuesto'),
        ('supplier_invoice', 'Factura de Proveedor'),
        ('customer_invoice', 'Factura de Cliente')
    ], string='Origen', default='manual', tracking=True)
    
    source_id = fields.Integer(string='ID Origen')
    source_reference = fields.Char(string='Referencia Origen', help="Referencia adicional del origen")
    
    # Referencias contables (MEJORADO)
    account_move_id = fields.Many2one('account.move', string='Factura/Asiento Contable')
    payment_id = fields.Many2one('account.payment', string='Pago')
    
    # Información adicional
    notes = fields.Text(string='Notas')
    tags = fields.Char(string='Etiquetas')
    
    # Campos para análisis
    category_id = fields.Many2one('cashflow.category', string='Categoría')
    subcategory = fields.Char(string='Subcategoría')
    
    # Control de realización
    actual_date = fields.Date(string='Fecha Real')
    actual_amount = fields.Monetary(string='Importe Real')
    variance = fields.Monetary(string='Variación', compute='_compute_variance', store=True)
    variance_percent = fields.Float(string='% Variación', compute='_compute_variance', store=True)
    
    # NUEVOS CAMPOS para integración con facturas
    payment_state = fields.Selection([
        ('not_applicable', 'No Aplica'),
        ('not_paid', 'No Pagado'),
        ('partial', 'Parcial'),
        ('paid', 'Pagado'),
        ('in_payment', 'En Proceso')
    ], string='Estado de Pago', default='not_applicable')
    
    invoice_date_due = fields.Date(string='Fecha Vencimiento Factura')
    amount_residual = fields.Monetary(string='Saldo Pendiente')

    # ====================================================================
    # CAMPOS COMPUTADOS
    # ====================================================================

    @api.depends('date')
    def _compute_period_fields(self):
        """Calcula campos de período para agrupaciones"""
        for record in self:
            if record.date:
                # Semana ISO
                year, week_num, _ = record.date.isocalendar()
                record.week = f"{year}-S{week_num:02d}"
                
                # Mes
                record.month = record.date.strftime('%Y-%m')
                
                # Trimestre
                quarter = (record.date.month - 1) // 3 + 1
                record.quarter = f"{record.date.year}-Q{quarter}"
                
                # Año
                record.year = str(record.date.year)
            else:
                record.week = record.month = record.quarter = record.year = False

    @api.depends('amount', 'actual_amount')
    def _compute_variance(self):
        """Calcula variaciones entre proyectado y real"""
        for record in self:
            if record.actual_amount:
                record.variance = record.actual_amount - record.amount
                if record.amount != 0:
                    record.variance_percent = (record.variance / record.amount) * 100
                else:
                    record.variance_percent = 0
            else:
                record.variance = 0
                record.variance_percent = 0

    # ====================================================================
    # VALIDACIONES
    # ====================================================================

    @api.constrains('amount')
    def _check_amount(self):
        for record in self:
            if record.amount == 0:
                raise ValidationError(_('El importe no puede ser cero'))

    @api.constrains('date', 'actual_date')
    def _check_dates(self):
        for record in self:
            if record.actual_date and record.date and record.actual_date < record.date:
                if abs((record.actual_date - record.date).days) > 30:
                    raise ValidationError(_('La fecha real no puede diferir más de 30 días de la fecha proyectada'))

    # ====================================================================
    # MÉTODOS DE ACCIÓN
    # ====================================================================

    def action_realize(self):
        """Marca la proyección como realizada"""
        for record in self:
            record.write({
                'state': 'realized',
                'actual_date': fields.Date.today(),
                'actual_amount': record.actual_amount or record.amount
            })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Proyecciones marcadas como realizadas'),
                'type': 'success'
            }
        }

    def action_cancel(self):
        """Cancela las proyecciones"""
        for record in self:
            record.write({'state': 'cancelled'})

    def action_confirm(self):
        """Confirma las proyecciones"""
        for record in self:
            record.write({'state': 'confirmed'})

    def action_view_related_invoice(self):
        """Ver factura relacionada si existe"""
        self.ensure_one()
        if self.account_move_id:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Factura Relacionada'),
                'res_model': 'account.move',
                'view_mode': 'form',
                'res_id': self.account_move_id.id,
                'target': 'current'
            }
        else:
            raise UserError(_('No hay factura relacionada con esta proyección'))

    # ====================================================================
    # MÉTODOS PARA IMPORTACIÓN DE FACTURAS
    # ====================================================================

    @api.model
    def import_from_invoices(self, invoice_ids=None, date_from=None, date_to=None):
        """NUEVA FUNCIONALIDAD: Importar facturas como proyecciones de cashflow"""
        
        domain = [
            ('state', '=', 'posted'),
            ('move_type', 'in', ['in_invoice', 'in_receipt', 'out_invoice', 'out_receipt']),
            ('payment_state', 'in', ['not_paid', 'partial'])
        ]
        
        if invoice_ids:
            domain.append(('id', 'in', invoice_ids))
        
        if date_from:
            domain.append(('invoice_date_due', '>=', date_from))
        
        if date_to:
            domain.append(('invoice_date_due', '<=', date_to))
        
        invoices = self.env['account.move'].search(domain)
        created_projections = []
        
        for invoice in invoices:
            # Determinar tipo de proyección
            if invoice.move_type in ['in_invoice', 'in_receipt']:
                projection_type = 'egreso'
                source_type = 'supplier_invoice'
                amount = -invoice.amount_residual  # Negativo para egresos
            else:  # out_invoice, out_receipt
                projection_type = 'ingreso'
                source_type = 'customer_invoice'
                amount = invoice.amount_residual
            
            # Verificar si ya existe proyección para esta factura
            existing = self.search([
                ('source_type', '=', source_type),
                ('account_move_id', '=', invoice.id)
            ])
            
            if existing:
                # Actualizar proyección existente
                existing.write({
                    'amount': amount,
                    'amount_residual': invoice.amount_residual,
                    'payment_state': invoice.payment_state,
                    'date': invoice.invoice_date_due or invoice.date,
                })
                created_projections.append(existing.id)
            else:
                # Crear nueva proyección
                projection_vals = {
                    'name': f"[{invoice.move_type.replace('_', ' ').title()}] {invoice.name}",
                    'partner_id': invoice.partner_id.id,
                    'date': invoice.invoice_date_due or invoice.date,
                    'type': projection_type,
                    'amount': amount,
                    'source_type': source_type,
                    'account_move_id': invoice.id,
                    'payment_state': invoice.payment_state,
                    'amount_residual': invoice.amount_residual,
                    'invoice_date_due': invoice.invoice_date_due,
                    'state': 'confirmed',
                    'company_id': invoice.company_id.id,
                    'fiscal_type': 'white',  # Por defecto, se puede personalizar
                    'source_reference': invoice.ref or invoice.name,
                    'notes': f"Importado automáticamente desde factura {invoice.name}"
                }
                
                projection = self.create(projection_vals)
                created_projections.append(projection.id)
        
        return {
            'created_count': len(created_projections),
            'projection_ids': created_projections
        }

    @api.model
    def update_from_invoices(self):
        """Actualizar proyecciones existentes basadas en cambios en facturas"""
        # Buscar proyecciones que provienen de facturas
        invoice_projections = self.search([
            ('source_type', 'in', ['supplier_invoice', 'customer_invoice']),
            ('account_move_id', '!=', False),
            ('state', 'not in', ['realized', 'cancelled'])
        ])
        
        updated_count = 0
        for projection in invoice_projections:
            invoice = projection.account_move_id
            if invoice.exists():
                # Verificar si la factura fue pagada completamente
                if invoice.payment_state == 'paid':
                    projection.write({
                        'state': 'realized',
                        'actual_date': invoice.payment_id.payment_date if invoice.payment_id else fields.Date.today(),
                        'actual_amount': projection.amount,
                        'payment_state': 'paid'
                    })
                    updated_count += 1
                else:
                    # Actualizar montos y estado de pago
                    new_amount = -invoice.amount_residual if projection.type == 'egreso' else invoice.amount_residual
                    if abs(projection.amount - new_amount) > 0.01:  # Si hay diferencia significativa
                        projection.write({
                            'amount': new_amount,
                            'amount_residual': invoice.amount_residual,
                            'payment_state': invoice.payment_state
                        })
                        updated_count += 1
        
        return updated_count

    @api.model
    def generate_from_periodic_expenses(self):
        """Generar proyecciones desde gastos periódicos activos"""
        expenses = self.env['periodic.expense'].search([
            ('state', '=', 'active'),
            ('auto_create_cashflow', '=', True)
        ])
        
        created_count = 0
        for expense in expenses:
            # Crear proyección para el próximo vencimiento si no existe
            if expense.next_payment_date:
                existing = self.search([
                    ('source_type', '=', 'periodic'),
                    ('source_id', '=', expense.id),
                    ('date', '=', expense.next_payment_date)
                ])
                
                if not existing:
                    self.create({
                        'name': f"[Periódico] {expense.name}",
                        'partner_id': expense.partner_id.id,
                        'date': expense.next_payment_date,
                        'type': 'egreso',
                        'fiscal_type': expense.fiscal_type,
                        'amount': -expense.amount,
                        'source_type': 'periodic',
                        'source_id': expense.id,
                        'state': 'projected',
                        'category_id': expense.category_id.cashflow_category_id.id if hasattr(expense.category_id, 'cashflow_category_id') else False,
                        'company_id': expense.company_id.id,
                        'notes': f"Generado automáticamente desde gasto periódico"
                    })
                    created_count += 1
        
        return created_count

    # ====================================================================
    # MÉTODOS PARA ANÁLISIS Y REPORTES
    # ====================================================================

    @api.model
    def get_cashflow_analysis(self, date_from, date_to, group_by='month'):
        """Análisis de cashflow por períodos"""
        domain = [
            ('date', '>=', date_from),
            ('date', '<=', date_to),
            ('state', 'in', ['projected', 'confirmed', 'realized'])
        ]
        
        projections = self.search(domain)
        
        if group_by == 'week':
            group_field = 'week'
        elif group_by == 'quarter':
            group_field = 'quarter'
        elif group_by == 'year':
            group_field = 'year'
        else:
            group_field = 'month'
        
        # Agrupar datos
        grouped_data = {}
        for projection in projections:
            period = getattr(projection, group_field)
            if period not in grouped_data:
                grouped_data[period] = {
                    'ingreso_white': 0,
                    'ingreso_black': 0,
                    'egreso_white': 0,
                    'egreso_black': 0,
                    'total': 0
                }
            
            key = f"{projection.type}_{projection.fiscal_type}"
            grouped_data[period][key] += projection.amount
            grouped_data[period]['total'] += projection.amount
        
        return grouped_data

    def get_variance_analysis(self):
        """Análisis de variaciones entre proyectado y real"""
        realized = self.filtered(lambda x: x.state == 'realized' and x.actual_amount)
        
        total_projected = sum(realized.mapped('amount'))
        total_actual = sum(realized.mapped('actual_amount'))
        total_variance = total_actual - total_projected
        
        variance_by_type = {}
        for projection in realized:
            key = f"{projection.type}_{projection.fiscal_type}"
            if key not in variance_by_type:
                variance_by_type[key] = {
                    'projected': 0,
                    'actual': 0,
                    'variance': 0,
                    'count': 0
                }
            
            variance_by_type[key]['projected'] += projection.amount
            variance_by_type[key]['actual'] += projection.actual_amount
            variance_by_type[key]['variance'] += projection.variance
            variance_by_type[key]['count'] += 1
        
        return {
            'total_projected': total_projected,
            'total_actual': total_actual,
            'total_variance': total_variance,
            'variance_percent': (total_variance / total_projected * 100) if total_projected else 0,
            'by_type': variance_by_type
        }

    # ====================================================================
    # CRON JOBS Y MÉTODOS AUTOMÁTICOS
    # ====================================================================

    @api.model
    def cron_update_from_invoices(self):
        """Método para cron job: actualizar proyecciones desde facturas"""
        try:
            updated_count = self.update_from_invoices()
            _logger.info(f"Cashflow: {updated_count} proyecciones actualizadas desde facturas")
            return updated_count
        except Exception as e:
            _logger.error(f"Error en cron_update_from_invoices: {str(e)}")
            return False

    @api.model
    def cron_generate_from_periodic(self):
        """Método para cron job: generar proyecciones desde gastos periódicos"""
        try:
            created_count = self.generate_from_periodic_expenses()
            _logger.info(f"Cashflow: {created_count} proyecciones creadas desde gastos periódicos")
            return created_count
        except Exception as e:
            _logger.error(f"Error en cron_generate_from_periodic: {str(e)}")
            return False

    @api.model
    def clean_old_projections(self, days_old=365):
        """Limpiar proyecciones antiguas canceladas o realizadas"""
        cutoff_date = fields.Date.today() - timedelta(days=days_old)
        
        old_projections = self.search([
            ('date', '<', cutoff_date),
            ('state', 'in', ['cancelled', 'realized'])
        ])
        
        count = len(old_projections)
        old_projections.unlink()
        
        return count


# ====================================================================
# MODELO: CATEGORÍAS DE CASHFLOW
# ====================================================================

class CashflowCategory(models.Model):
    _name = 'cashflow.category'
    _description = 'Categorías de Cashflow'
    _order = 'sequence, name'

    name = fields.Char(string='Nombre', required=True)
    code = fields.Char(string='Código', required=True)
    sequence = fields.Integer(string='Secuencia', default=10)
    color = fields.Integer(string='Color', default=0)
    active = fields.Boolean(string='Activo', default=True)
    
    # Clasificación
    category_type = fields.Selection([
        ('operating', 'Operativo'),
        ('investing', 'Inversión'),
        ('financing', 'Financiamiento')
    ], string='Tipo de Categoría', default='operating')
    
    flow_type = fields.Selection([
        ('both', 'Ingresos y Egresos'),
        ('inflow', 'Solo Ingresos'),
        ('outflow', 'Solo Egresos')
    ], string='Tipo de Flujo', default='both')
    
    # Configuración contable
    default_account_ids = fields.Many2many(
        'account.account', 
        string='Cuentas por Defecto',
        help="Cuentas contables asociadas a esta categoría"
    )
    
    description = fields.Text(string='Descripción')
    
    # Estadísticas
    projection_count = fields.Integer(string='Proyecciones', compute='_compute_stats')
    total_projected = fields.Monetary(string='Total Proyectado', compute='_compute_stats')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    @api.constrains('code')
    def _check_code_unique(self):
        for category in self:
            if self.search_count([('code', '=', category.code), ('id', '!=', category.id)]) > 0:
                raise ValidationError(_('El código de categoría debe ser único'))

    def _compute_stats(self):
        for category in self:
            projections = self.env['cashflow.projection'].search([
                ('category_id', '=', category.id),
                ('state', 'in', ['projected', 'confirmed'])
            ])
            
            category.projection_count = len(projections)
            category.total_projected = sum(projections.mapped('amount'))

    def action_view_projections(self):
        """Ver proyecciones de esta categoría"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Proyecciones - %s') % self.name,
            'res_model': 'cashflow.projection',
            'view_mode': 'list,form',
            'domain': [('category_id', '=', self.id)],
            'context': {'default_category_id': self.id}
        }


# ====================================================================
# MODELO: INTEGRACIÓN CON ACCOUNT.MOVE
# ====================================================================

class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    # Campos para integración con cashflow
    cashflow_projection_ids = fields.One2many('cashflow.projection', 'account_move_id', 
                                              string='Proyecciones de Cashflow')
    cashflow_projection_count = fields.Integer(string='Proyecciones', compute='_compute_cashflow_count')
    
    def _compute_cashflow_count(self):
        for move in self:
            move.cashflow_projection_count = len(move.cashflow_projection_ids)

    def action_view_cashflow_projections(self):
        """Ver proyecciones de cashflow relacionadas con esta factura"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Proyecciones de Cashflow'),
            'res_model': 'cashflow.projection',
            'view_mode': 'list,form',
            'domain': [('account_move_id', '=', self.id)],
            'context': {
                'default_account_move_id': self.id,
                'create': False
            }
        }

    def action_create_cashflow_projection(self):
        """Crear proyección de cashflow desde esta factura"""
        self.ensure_one()
        
        if self.move_type in ['in_invoice', 'in_receipt']:
            projection_type = 'egreso'
            amount = -self.amount_residual
        elif self.move_type in ['out_invoice', 'out_receipt']:
            projection_type = 'ingreso'
            amount = self.amount_residual
        else:
            raise UserError(_('Este tipo de documento no puede generar proyecciones de cashflow'))
        
        projection = self.env['cashflow.projection'].create({
            'name': f"[{self.move_type.replace('_', ' ').title()}] {self.name}",
            'partner_id': self.partner_id.id,
            'date': self.invoice_date_due or self.date,
            'type': projection_type,
            'amount': amount,
            'source_type': 'supplier_invoice' if projection_type == 'egreso' else 'customer_invoice',
            'account_move_id': self.id,
            'payment_state': self.payment_state,
            'amount_residual': self.amount_residual,
            'invoice_date_due': self.invoice_date_due,
            'state': 'confirmed',
            'company_id': self.company_id.id,
            'source_reference': self.ref or self.name,
        })
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Proyección Creada'),
            'res_model': 'cashflow.projection',
            'view_mode': 'form',
            'res_id': projection.id,
            'target': 'current'
        }

import logging
_logger = logging.getLogger(__name__)