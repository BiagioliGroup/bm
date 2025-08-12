# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class PeriodicExpense(models.Model):
    _name = 'periodic.expense'
    _description = 'Gastos Periódicos'
    _order = 'next_payment_date desc, priority desc'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Información básica
    name = fields.Char(string='Descripción del Gasto', required=True, tracking=True)
    partner_id = fields.Many2one('res.partner', string='Proveedor', required=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company, required=True)
    
    # Categorización
    category_id = fields.Many2one('expense.category', string='Categoría', required=True, tracking=True)
    expense_type = fields.Selection([
        ('tax', 'Impuestos'),
        ('professional', 'Honorarios Profesionales'),
        ('service', 'Servicios'),
        ('supply', 'Suministros'),
        ('maintenance', 'Mantenimiento'),
        ('insurance', 'Seguros'),
        ('rental', 'Alquileres'),
        ('other', 'Otros')
    ], string='Tipo de Gasto', required=True, tracking=True)
    
    # Periodicidad
    frequency = fields.Selection([
        ('weekly', 'Semanal'),
        ('biweekly', 'Quincenal'),
        ('monthly', 'Mensual'),
        ('bimonthly', 'Bimestral'),
        ('quarterly', 'Trimestral'),
        ('biannual', 'Semestral'),
        ('annual', 'Anual')
    ], string='Frecuencia', default='monthly', required=True, tracking=True)
    
    # Montos y fechas
    amount = fields.Monetary(string='Monto', required=True, tracking=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True)
    
    start_date = fields.Date(string='Fecha de Inicio', required=True, default=fields.Date.today, tracking=True)
    next_payment_date = fields.Date(string='Próximo Vencimiento', compute='_compute_next_payment_date', store=True)
    last_payment_date = fields.Date(string='Último Pago', tracking=True)
    
    # Control de estado
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('active', 'Activo'),
        ('pending', 'Pendiente'),
        ('paid', 'Pagado'),
        ('suspended', 'Suspendido'),
        ('cancelled', 'Cancelado')
    ], string='Estado', default='draft', tracking=True)
    
    # Clasificación fiscal
    fiscal_type = fields.Selection([
        ('white', 'En Blanco'),
        ('black', 'En Negro')
    ], string='Tipo Fiscal', default='white', required=True, tracking=True)
    
    # Control mensual
    monthly_control_ids = fields.One2many('periodic.expense.monthly', 'expense_id', string='Control Mensual')
    
    # Configuración
    auto_generate_invoice = fields.Boolean(string='Auto-generar Factura', default=False)
    auto_create_cashflow = fields.Boolean(string='Auto-crear Proyección Cashflow', default=True, 
                                          help="Crear automáticamente proyecciones en el cashflow")
    journal_id = fields.Many2one('account.journal', string='Diario Contable', 
                                 domain="[('company_id', '=', company_id)]")
    account_id = fields.Many2one('account.account', string='Cuenta Contable',
                                 domain="[('company_id', '=', company_id)]")
    
    # Prioridad y alertas
    priority = fields.Selection([
        ('0', 'Baja'),
        ('1', 'Normal'),
        ('2', 'Alta'),
        ('3', 'Crítica')
    ], string='Prioridad', default='1', tracking=True)
    
    alert_days = fields.Integer(string='Días de Alerta', default=7,
                                help="Días antes del vencimiento para crear alertas")
    
    # Campos computados
    is_overdue = fields.Boolean(string='Vencido', compute='_compute_overdue', store=True)
    days_until_due = fields.Integer(string='Días hasta Vencimiento', compute='_compute_overdue', store=True)
    monthly_average = fields.Monetary(string='Promedio Mensual', compute='_compute_monthly_average')
    
    # Contadores estadísticos
    invoice_count = fields.Integer(string='Facturas Creadas', compute='_compute_invoice_count')
    payment_count = fields.Integer(string='Pagos Realizados', compute='_compute_payment_count')

    @api.depends('start_date', 'frequency', 'last_payment_date', 'state')
    def _compute_next_payment_date(self):
        """Calcula la próxima fecha de pago basada en la frecuencia"""
        for expense in self:
            if expense.state in ['cancelled', 'suspended']:
                expense.next_payment_date = False
                continue
                
            base_date = expense.last_payment_date or expense.start_date
            if not base_date:
                expense.next_payment_date = False
                continue
                
            frequency_map = {
                'weekly': relativedelta(weeks=1),
                'biweekly': relativedelta(weeks=2),
                'monthly': relativedelta(months=1),
                'bimonthly': relativedelta(months=2),
                'quarterly': relativedelta(months=3),
                'biannual': relativedelta(months=6),
                'annual': relativedelta(years=1)
            }
            
            delta = frequency_map.get(expense.frequency, relativedelta(months=1))
            expense.next_payment_date = base_date + delta

    @api.depends('next_payment_date')
    def _compute_overdue(self):
        """Determina si el gasto está vencido"""
        today = fields.Date.today()
        for expense in self:
            if expense.next_payment_date:
                expense.days_until_due = (expense.next_payment_date - today).days
                expense.is_overdue = expense.next_payment_date < today and expense.state == 'pending'
            else:
                expense.days_until_due = 0
                expense.is_overdue = False

    @api.depends('amount', 'frequency')
    def _compute_monthly_average(self):
        """Calcula el promedio mensual según la frecuencia"""
        frequency_divisors = {
            'weekly': 0.23,    # ~4.33 semanas por mes
            'biweekly': 0.46,  # ~2.17 quincenas por mes
            'monthly': 1,
            'bimonthly': 2,
            'quarterly': 3,
            'biannual': 6,
            'annual': 12
        }
        
        for expense in self:
            divisor = frequency_divisors.get(expense.frequency, 1)
            expense.monthly_average = expense.amount / divisor if divisor else expense.amount

    def _compute_invoice_count(self):
        """Cuenta facturas relacionadas con este gasto"""
        for expense in self:
            # Buscar facturas que tengan referencia a este gasto periódico
            expense.invoice_count = self.env['account.move'].search_count([
                ('ref', 'ilike', expense.name),
                ('partner_id', '=', expense.partner_id.id),
                ('company_id', '=', expense.company_id.id)
            ])

    def _compute_payment_count(self):
        """Cuenta pagos realizados para este gasto"""
        for expense in self:
            expense.payment_count = len(expense.monthly_control_ids.filtered(lambda x: x.state == 'paid'))

    # ====================================================================
    # VALIDACIONES
    # ====================================================================

    @api.constrains('amount')
    def _check_amount(self):
        for expense in self:
            if expense.amount <= 0:
                raise ValidationError(_('El monto debe ser mayor a cero'))

    @api.constrains('start_date', 'last_payment_date')
    def _check_dates(self):
        for expense in self:
            if expense.last_payment_date and expense.start_date and expense.last_payment_date < expense.start_date:
                raise ValidationError(_('La fecha del último pago no puede ser anterior a la fecha de inicio'))

    # ====================================================================
    # MÉTODOS DE ACCIÓN (BOTONES)
    # ====================================================================

    def action_activate(self):
        """Activa el gasto periódico y genera controles mensuales"""
        for expense in self:
            expense.write({'state': 'active'})
            expense._generate_monthly_controls()
            expense._create_cashflow_projections()
            
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Gasto activado y controles generados exitosamente'),
                'type': 'success'
            }
        }

    def action_suspend(self):
        """Suspende el gasto periódico"""
        for expense in self:
            expense.write({'state': 'suspended'})
            # Cancelar proyecciones futuras en el cashflow
            expense._cancel_future_cashflow_projections()

    def action_cancel(self):
        """Cancela el gasto periódico"""
        for expense in self:
            expense.write({'state': 'cancelled'})
            # Cancelar todas las proyecciones en el cashflow
            expense._cancel_future_cashflow_projections()

    def action_mark_paid(self):
        """Marca como pagado y actualiza fechas"""
        for expense in self:
            expense.write({
                'state': 'active',
                'last_payment_date': fields.Date.today()
            })
            expense._compute_next_payment_date()
            
            # Crear control mensual para este pago
            expense._create_monthly_control_for_payment()

    def action_create_invoice(self):
        """Crear factura de proveedor para este gasto"""
        self.ensure_one()
        
        if not self.partner_id:
            raise UserError(_('Debe definir un proveedor para crear la factura'))
        
        invoice_vals = {
            'move_type': 'in_invoice',
            'partner_id': self.partner_id.id,
            'invoice_date': fields.Date.today(),
            'invoice_date_due': self.next_payment_date or fields.Date.today(),
            'ref': f'Gasto Periódico: {self.name}',
            'company_id': self.company_id.id,
            'journal_id': self.journal_id.id if self.journal_id else None,
            'invoice_line_ids': [(0, 0, {
                'name': self.name,
                'quantity': 1,
                'price_unit': self.amount,
                'account_id': self.account_id.id if self.account_id else self.partner_id.property_account_payable_id.id,
            })]
        }
        
        invoice = self.env['account.move'].create(invoice_vals)
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Factura Generada'),
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': invoice.id,
            'target': 'current'
        }

    def action_view_invoices(self):
        """Ver facturas relacionadas con este gasto"""
        self.ensure_one()
        
        invoices = self.env['account.move'].search([
            ('ref', 'ilike', self.name),
            ('partner_id', '=', self.partner_id.id),
            ('company_id', '=', self.company_id.id)
        ])
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Facturas Relacionadas'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', invoices.ids)],
            'context': {'create': False}
        }
    
    def action_view_cashflow_projections(self):
        """Ver proyecciones de cashflow relacionadas con este gasto periódico"""
        self.ensure_one()
        
        # Buscar proyecciones existentes para este gasto
        projections = self.env['cashflow.projection'].search([
            ('source_type', '=', 'periodic'),
            ('source_id', '=', self.id)
        ])
        
        action = {
            'type': 'ir.actions.act_window',
            'name': _('Proyecciones de Cashflow: %s') % self.name,
            'res_model': 'cashflow.projection',
            'domain': [('source_type', '=', 'periodic'), ('source_id', '=', self.id)],
            'context': {
                'default_source_type': 'periodic',
                'default_source_id': self.id,
                'default_name': f'[Periódico] {self.name}',
                'default_partner_id': self.partner_id.id,
                'default_type': 'egreso',
                'default_fiscal_type': self.fiscal_type,
                'search_default_from_periodic': 1
            },
        }
        
        if len(projections) == 1:
            # Si hay solo una proyección, abrir directamente en vista formulario
            action.update({
                'view_mode': 'form',
                'res_id': projections.id,
            })
        else:
            # Si hay múltiples o ninguna, mostrar vista lista
            action.update({
                'view_mode': 'list,form',
            })
            
        return action

    # ====================================================================
    # MÉTODOS PRIVADOS
    # ====================================================================

    def _generate_monthly_controls(self):
        """Genera controles mensuales para seguimiento individualizado"""
        for expense in self:
            # Generar controles para los próximos 12 meses
            current_date = fields.Date.today().replace(day=1)  # Primer día del mes actual
            
            for i in range(12):
                month_date = current_date + relativedelta(months=i)
                
                # Verificar si ya existe control para este mes
                existing = self.env['periodic.expense.monthly'].search([
                    ('expense_id', '=', expense.id),
                    ('month_date', '=', month_date)
                ])
                
                if not existing:
                    self.env['periodic.expense.monthly'].create({
                        'expense_id': expense.id,
                        'month_date': month_date,
                        'expected_amount': expense.amount,
                        'state': 'pending'
                    })

    def _create_cashflow_projections(self):
        """Crear proyecciones en el cashflow para los próximos pagos"""
        for expense in self:
            if not expense.auto_create_cashflow:
                continue
                
            # Crear proyecciones para los próximos 6 meses
            current_date = expense.next_payment_date or fields.Date.today()
            
            for i in range(6):
                projection_date = current_date
                if expense.frequency == 'monthly':
                    projection_date = current_date + relativedelta(months=i)
                elif expense.frequency == 'bimonthly':
                    projection_date = current_date + relativedelta(months=i*2)
                elif expense.frequency == 'quarterly':
                    projection_date = current_date + relativedelta(months=i*3)
                elif expense.frequency == 'biannual':
                    projection_date = current_date + relativedelta(months=i*6)
                elif expense.frequency == 'annual':
                    projection_date = current_date + relativedelta(years=i)
                
                # Verificar que no exista ya una proyección para esta fecha
                existing = self.env['cashflow.projection'].search([
                    ('source_type', '=', 'periodic'),
                    ('source_id', '=', expense.id),
                    ('date', '=', projection_date)
                ])
                
                if not existing:
                    self.env['cashflow.projection'].create({
                        'name': f"[Periódico] {expense.name}",
                        'partner_id': expense.partner_id.id,
                        'date': projection_date,
                        'type': 'egreso',
                        'fiscal_type': expense.fiscal_type,
                        'amount': -expense.amount,  # Negativo porque es egreso
                        'source_type': 'periodic',
                        'source_id': expense.id,
                        'state': 'projected',
                        'category_id': expense.category_id.cashflow_category_id.id if hasattr(expense.category_id, 'cashflow_category_id') else False,
                        'company_id': expense.company_id.id
                    })

    def _cancel_future_cashflow_projections(self):
        """Cancelar proyecciones futuras en el cashflow"""
        for expense in self:
            future_projections = self.env['cashflow.projection'].search([
                ('source_type', '=', 'periodic'),
                ('source_id', '=', expense.id),
                ('date', '>=', fields.Date.today()),
                ('state', 'in', ['draft', 'projected'])
            ])
            future_projections.unlink()

    def _create_monthly_control_for_payment(self):
        """Crear control mensual cuando se marca como pagado"""
        for expense in self:
            current_month = fields.Date.today().replace(day=1)
            
            existing = self.env['periodic.expense.monthly'].search([
                ('expense_id', '=', expense.id),
                ('month_date', '=', current_month)
            ])
            
            if existing:
                existing.write({
                    'state': 'paid',
                    'payment_date': fields.Date.today(),
                    'actual_amount': expense.amount
                })
            else:
                self.env['periodic.expense.monthly'].create({
                    'expense_id': expense.id,
                    'month_date': current_month,
                    'expected_amount': expense.amount,
                    'actual_amount': expense.amount,
                    'state': 'paid',
                    'payment_date': fields.Date.today()
                })


# ====================================================================
# MODELO: CONTROL MENSUAL DE GASTOS PERIÓDICOS
# ====================================================================

class PeriodicExpenseMonthly(models.Model):
    _name = 'periodic.expense.monthly'
    _description = 'Control Mensual de Gastos Periódicos'
    _order = 'month_date desc'
    _rec_name = 'display_name'

    expense_id = fields.Many2one('periodic.expense', string='Gasto Periódico', required=True, ondelete='cascade')
    month_date = fields.Date(string='Mes', required=True)
    
    # Control de estado mensual
    state = fields.Selection([
        ('pending', 'Pendiente'),
        ('invoice_received', 'Factura Recibida'),
        ('paid', 'Pagado')
    ], string='Estado', default='pending')
    
    # Montos
    expected_amount = fields.Monetary(string='Monto Esperado')
    actual_amount = fields.Monetary(string='Monto Real')
    difference = fields.Monetary(string='Diferencia', compute='_compute_difference', store=True)
    
    currency_id = fields.Many2one('res.currency', related='expense_id.currency_id', store=True)
    
    # Referencias contables
    invoice_id = fields.Many2one('account.move', string='Factura')
    payment_id = fields.Many2one('account.payment', string='Pago')
    
    # Fechas de control
    invoice_date = fields.Date(string='Fecha Factura')
    payment_date = fields.Date(string='Fecha Pago')
    due_date = fields.Date(string='Fecha Vencimiento')
    
    # Información adicional
    notes = fields.Text(string='Observaciones')
    
    # Campos computados
    display_name = fields.Char(compute='_compute_display_name', store=True)
    is_late = fields.Boolean(string='Atrasado', compute='_compute_late_status')

    @api.depends('expense_id.name', 'month_date')
    def _compute_display_name(self):
        for record in self:
            month_str = record.month_date.strftime('%m/%Y') if record.month_date else ''
            record.display_name = f"{record.expense_id.name or ''} - {month_str}"

    @api.depends('expected_amount', 'actual_amount')
    def _compute_difference(self):
        for record in self:
            record.difference = (record.actual_amount or 0) - (record.expected_amount or 0)

    @api.depends('due_date', 'state')
    def _compute_late_status(self):
        today = fields.Date.today()
        for record in self:
            record.is_late = (record.due_date and 
                              record.due_date < today and 
                              record.state != 'paid')

    def action_mark_invoice_received(self):
        """Marca que se recibió la factura"""
        for record in self:
            record.write({
                'state': 'invoice_received',
                'invoice_date': fields.Date.today()
            })

    def action_mark_paid(self):
        """Marca como pagado"""
        for record in self:
            record.write({
                'state': 'paid',
                'payment_date': fields.Date.today(),
                'actual_amount': record.actual_amount or record.expected_amount
            })


# ====================================================================
# MODELO: CATEGORÍAS DE GASTOS PERIÓDICOS
# ====================================================================

class ExpenseCategory(models.Model):
    _name = 'expense.category'
    _description = 'Categorías de Gastos Periódicos'
    _order = 'name'

    name = fields.Char(string='Nombre', required=True)
    code = fields.Char(string='Código', required=True)
    description = fields.Text(string='Descripción')
    color = fields.Integer(string='Color', default=0)
    active = fields.Boolean(string='Activo', default=True)
    
    # Configuración contable por defecto
    default_journal_id = fields.Many2one('account.journal', string='Diario por Defecto',
                                         domain="[('type', '=', 'purchase')]")
    default_account_id = fields.Many2one('account.account', string='Cuenta por Defecto')
    
    # Relación con categorías de cashflow
    cashflow_category_id = fields.Many2one('cashflow.category', string='Categoría de Cashflow')
    
    # Estadísticas
    expense_count = fields.Integer(string='Cantidad de Gastos', compute='_compute_expense_count')
    total_monthly_amount = fields.Monetary(string='Total Mensual', compute='_compute_totals')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    @api.constrains('code')
    def _check_code_unique(self):
        for category in self:
            if self.search_count([('code', '=', category.code), ('id', '!=', category.id)]) > 0:
                raise ValidationError(_('El código de categoría debe ser único'))

    def _compute_expense_count(self):
        for category in self:
            category.expense_count = self.env['periodic.expense'].search_count([
                ('category_id', '=', category.id),
                ('state', 'not in', ['cancelled'])
            ])

    def _compute_totals(self):
        for category in self:
            expenses = self.env['periodic.expense'].search([
                ('category_id', '=', category.id),
                ('state', 'in', ['active', 'pending'])
            ])
            
            # Calcular total mensual promedio
            monthly_total = 0
            for expense in expenses:
                monthly_total += expense.monthly_average
                    
            category.total_monthly_amount = monthly_total

    def action_view_expenses(self):
        """Ver gastos de esta categoría"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Gastos de la Categoría: %s') % self.name,
            'res_model': 'periodic.expense',
            'view_mode': 'list,form',
            'domain': [('category_id', '=', self.id)],
            'context': {'default_category_id': self.id}
        }