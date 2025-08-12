# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class FinancialDashboard(models.Model):
    _name = 'financial.dashboard'
    _description = 'Dashboard Principal Financiero'
    _rec_name = 'display_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    display_name = fields.Char(string='Nombre', compute='_compute_display_name', store=True)
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company)
    
    # Campos para dashboard - Caja y Bancos
    total_cash_bank = fields.Monetary(string='Total Caja y Bancos', compute='_compute_totals')
    total_cash_white = fields.Monetary(string='Efectivo en Blanco', compute='_compute_totals')
    total_cash_black = fields.Monetary(string='Efectivo en Negro', compute='_compute_totals')
    total_bank_white = fields.Monetary(string='Bancos en Blanco', compute='_compute_totals')
    total_bank_black = fields.Monetary(string='Bancos en Negro', compute='_compute_totals')
    
    # Gastos periódicos pendientes
    pending_expenses_count = fields.Integer(string='Gastos Pendientes', compute='_compute_pending_expenses')
    overdue_expenses_count = fields.Integer(string='Gastos Vencidos', compute='_compute_pending_expenses')
    
    # INTEGRACIÓN CON FACTURAS DE ACCOUNT.MOVE
    # Facturas de Proveedores
    supplier_invoices_draft = fields.Integer(string='Facturas Prov. Borrador', compute='_compute_invoice_stats')
    supplier_invoices_posted = fields.Integer(string='Facturas Prov. Confirmadas', compute='_compute_invoice_stats')
    supplier_invoices_not_paid = fields.Integer(string='Facturas Prov. No Pagadas', compute='_compute_invoice_stats')
    supplier_invoices_partial = fields.Integer(string='Facturas Prov. Parciales', compute='_compute_invoice_stats')
    supplier_invoices_paid = fields.Integer(string='Facturas Prov. Pagadas', compute='_compute_invoice_stats')
    
    # Facturas de Clientes  
    customer_invoices_draft = fields.Integer(string='Facturas Cli. Borrador', compute='_compute_invoice_stats')
    customer_invoices_posted = fields.Integer(string='Facturas Cli. Confirmadas', compute='_compute_invoice_stats')
    customer_invoices_not_paid = fields.Integer(string='Facturas Cli. No Pagadas', compute='_compute_invoice_stats')
    customer_invoices_partial = fields.Integer(string='Facturas Cli. Parciales', compute='_compute_invoice_stats')
    customer_invoices_paid = fields.Integer(string='Facturas Cli. Pagadas', compute='_compute_invoice_stats')
    
    # Montos pendientes de cobro/pago
    supplier_amount_due = fields.Monetary(string='Total por Pagar Proveedores', compute='_compute_invoice_amounts')
    customer_amount_due = fields.Monetary(string='Total por Cobrar Clientes', compute='_compute_invoice_amounts')
    
    # Proyecciones
    monthly_projection = fields.Monetary(string='Proyección Mensual', compute='_compute_projections')
    weekly_projection = fields.Monetary(string='Proyección Semanal', compute='_compute_projections')
    
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True)
    
    # Dashboard JSON data
    kanban_dashboard = fields.Text(compute='_compute_kanban_dashboard')
    dashboard_graph = fields.Text(compute='_compute_dashboard_graph')

    @api.depends('company_id')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"Dashboard Financiero - {record.company_id.name}"

    def _compute_totals(self):
        """Calcula totales de caja y bancos separados por blanco/negro"""
        for record in self:
            # Obtener journals de caja y banco
            cash_journals = self.env['account.journal'].search([
                ('type', 'in', ['cash', 'bank']),
                ('company_id', '=', record.company_id.id)
            ])
            
            total_white = total_black = 0
            cash_white = cash_black = bank_white = bank_black = 0
            
            for journal in cash_journals:
                balance = journal.default_account_id.balance if journal.default_account_id else 0
                
                # Clasificar por tags o categorías personalizadas
                # Puedes ajustar esta lógica según tu criterio de clasificación
                is_black = (
                    journal.name and ('negro' in journal.name.lower() or 'black' in journal.name.lower()) or
                    journal.code and ('NEG' in journal.code.upper() or 'BLK' in journal.code.upper())
                )
                
                if is_black:
                    total_black += balance
                    if journal.type == 'cash':
                        cash_black += balance
                    else:
                        bank_black += balance
                else:
                    total_white += balance
                    if journal.type == 'cash':
                        cash_white += balance
                    else:
                        bank_white += balance
            
            record.total_cash_bank = total_white + total_black
            record.total_cash_white = cash_white
            record.total_cash_black = cash_black
            record.total_bank_white = bank_white
            record.total_bank_black = bank_black

    def _compute_pending_expenses(self):
        """Calcula gastos periódicos pendientes"""
        for record in self:
            today = fields.Date.today()
            
            pending = self.env['periodic.expense'].search_count([
                ('company_id', '=', record.company_id.id),
                ('state', '=', 'pending'),
                ('next_payment_date', '<=', today + timedelta(days=7))
            ])
            
            overdue = self.env['periodic.expense'].search_count([
                ('company_id', '=', record.company_id.id),
                ('state', '=', 'pending'),
                ('next_payment_date', '<', today)
            ])
            
            record.pending_expenses_count = pending
            record.overdue_expenses_count = overdue

    def _compute_invoice_stats(self):
        """NUEVA FUNCIONALIDAD: Calcula estadísticas de facturas desde account.move"""
        for record in self:
            # Facturas de Proveedores (in_invoice, in_receipt)
            supplier_domain = [
                ('company_id', '=', record.company_id.id),
                ('move_type', 'in', ['in_invoice', 'in_receipt'])
            ]
            
            # Por estado del documento
            record.supplier_invoices_draft = self.env['account.move'].search_count(
                supplier_domain + [('state', '=', 'draft')]
            )
            record.supplier_invoices_posted = self.env['account.move'].search_count(
                supplier_domain + [('state', '=', 'posted')]
            )
            
            # Por estado de pago (solo facturas confirmadas)
            posted_supplier_domain = supplier_domain + [('state', '=', 'posted')]
            record.supplier_invoices_not_paid = self.env['account.move'].search_count(
                posted_supplier_domain + [('payment_state', '=', 'not_paid')]
            )
            record.supplier_invoices_partial = self.env['account.move'].search_count(
                posted_supplier_domain + [('payment_state', '=', 'partial')]
            )
            record.supplier_invoices_paid = self.env['account.move'].search_count(
                posted_supplier_domain + [('payment_state', '=', 'paid')]
            )
            
            # Facturas de Clientes (out_invoice, out_receipt)
            customer_domain = [
                ('company_id', '=', record.company_id.id),
                ('move_type', 'in', ['out_invoice', 'out_receipt'])
            ]
            
            # Por estado del documento
            record.customer_invoices_draft = self.env['account.move'].search_count(
                customer_domain + [('state', '=', 'draft')]
            )
            record.customer_invoices_posted = self.env['account.move'].search_count(
                customer_domain + [('state', '=', 'posted')]
            )
            
            # Por estado de pago (solo facturas confirmadas)
            posted_customer_domain = customer_domain + [('state', '=', 'posted')]
            record.customer_invoices_not_paid = self.env['account.move'].search_count(
                posted_customer_domain + [('payment_state', '=', 'not_paid')]
            )
            record.customer_invoices_partial = self.env['account.move'].search_count(
                posted_customer_domain + [('payment_state', '=', 'partial')]
            )
            record.customer_invoices_paid = self.env['account.move'].search_count(
                posted_customer_domain + [('payment_state', '=', 'paid')]
            )

    def _compute_invoice_amounts(self):
        """NUEVA FUNCIONALIDAD: Calcula montos pendientes de pago/cobro"""
        for record in self:
            # Facturas de proveedores pendientes de pago (confirmadas y no pagadas totalmente)
            supplier_invoices = self.env['account.move'].search([
                ('company_id', '=', record.company_id.id),
                ('move_type', 'in', ['in_invoice', 'in_receipt']),
                ('state', '=', 'posted'),
                ('payment_state', 'in', ['not_paid', 'partial']),
                ('amount_residual', '>', 0)
            ])
            record.supplier_amount_due = sum(supplier_invoices.mapped('amount_residual'))
            
            # Facturas de clientes pendientes de cobro (confirmadas y no cobradas totalmente)
            customer_invoices = self.env['account.move'].search([
                ('company_id', '=', record.company_id.id),
                ('move_type', 'in', ['out_invoice', 'out_receipt']),
                ('state', '=', 'posted'),
                ('payment_state', 'in', ['not_paid', 'partial']),
                ('amount_residual', '>', 0)
            ])
            record.customer_amount_due = sum(customer_invoices.mapped('amount_residual'))

    def _compute_projections(self):
        """Calcula proyecciones de cashflow incluyendo facturas pendientes"""
        for record in self:
            today = fields.Date.today()
            end_month = today + relativedelta(months=1)
            end_week = today + timedelta(days=7)
            
            # Proyección mensual desde cashflow manual
            monthly_in = sum(self.env['cashflow.projection'].search([
                ('company_id', '=', record.company_id.id),
                ('date', '>=', today),
                ('date', '<=', end_month),
                ('type', '=', 'ingreso')
            ]).mapped('amount'))
            
            monthly_out = sum(self.env['cashflow.projection'].search([
                ('company_id', '=', record.company_id.id),
                ('date', '>=', today),
                ('date', '<=', end_month),
                ('type', '=', 'egreso')
            ]).mapped('amount'))
            
            # Proyección semanal desde cashflow manual
            weekly_in = sum(self.env['cashflow.projection'].search([
                ('company_id', '=', record.company_id.id),
                ('date', '>=', today),
                ('date', '<=', end_week),
                ('type', '=', 'ingreso')
            ]).mapped('amount'))
            
            weekly_out = sum(self.env['cashflow.projection'].search([
                ('company_id', '=', record.company_id.id),
                ('date', '>=', today),
                ('date', '<=', end_week),
                ('type', '=', 'egreso')
            ]).mapped('amount'))
            
            # AGREGAR facturas pendientes a las proyecciones
            # Facturas de proveedores con vencimiento en el período
            supplier_monthly = sum(self.env['account.move'].search([
                ('company_id', '=', record.company_id.id),
                ('move_type', 'in', ['in_invoice', 'in_receipt']),
                ('state', '=', 'posted'),
                ('payment_state', 'in', ['not_paid', 'partial']),
                ('invoice_date_due', '>=', today),
                ('invoice_date_due', '<=', end_month)
            ]).mapped('amount_residual'))
            
            supplier_weekly = sum(self.env['account.move'].search([
                ('company_id', '=', record.company_id.id),
                ('move_type', 'in', ['in_invoice', 'in_receipt']),
                ('state', '=', 'posted'),
                ('payment_state', 'in', ['not_paid', 'partial']),
                ('invoice_date_due', '>=', today),
                ('invoice_date_due', '<=', end_week)
            ]).mapped('amount_residual'))
            
            # Facturas de clientes con vencimiento en el período
            customer_monthly = sum(self.env['account.move'].search([
                ('company_id', '=', record.company_id.id),
                ('move_type', 'in', ['out_invoice', 'out_receipt']),
                ('state', '=', 'posted'),
                ('payment_state', 'in', ['not_paid', 'partial']),
                ('invoice_date_due', '>=', today),
                ('invoice_date_due', '<=', end_month)
            ]).mapped('amount_residual'))
            
            customer_weekly = sum(self.env['account.move'].search([
                ('company_id', '=', record.company_id.id),
                ('move_type', 'in', ['out_invoice', 'out_receipt']),
                ('state', '=', 'posted'),
                ('payment_state', 'in', ['not_paid', 'partial']),
                ('invoice_date_due', '>=', today),
                ('invoice_date_due', '<=', end_week)
            ]).mapped('amount_residual'))
            
            # Totales: ingresos - egresos (incluye facturas)
            record.monthly_projection = (monthly_in + customer_monthly) - (monthly_out + supplier_monthly)
            record.weekly_projection = (weekly_in + customer_weekly) - (weekly_out + supplier_weekly)

    def _compute_kanban_dashboard(self):
        """Genera datos para el dashboard kanban"""
        for record in self:
            dashboard_data = {
                'currency_id': record.currency_id.id,
                'total_cash_bank': record.total_cash_bank,
                'cash_breakdown': {
                    'white': {
                        'cash': record.total_cash_white,
                        'bank': record.total_bank_white
                    },
                    'black': {
                        'cash': record.total_cash_black,
                        'bank': record.total_bank_black
                    }
                },
                'expenses': {
                    'pending': record.pending_expenses_count,
                    'overdue': record.overdue_expenses_count
                },
                'supplier_invoices': {
                    'draft': record.supplier_invoices_draft,
                    'not_paid': record.supplier_invoices_not_paid,
                    'partial': record.supplier_invoices_partial,
                    'amount_due': record.supplier_amount_due
                },
                'customer_invoices': {
                    'draft': record.customer_invoices_draft,
                    'not_paid': record.customer_invoices_not_paid,
                    'partial': record.customer_invoices_partial,
                    'amount_due': record.customer_amount_due
                },
                'projections': {
                    'monthly': record.monthly_projection,
                    'weekly': record.weekly_projection
                }
            }
            record.kanban_dashboard = json.dumps(dashboard_data)

    def _compute_dashboard_graph(self):
        """Genera datos para gráficos del dashboard"""
        for record in self:
            # Datos para gráfico de evolución de caja últimos 30 días
            graph_data = record._get_cash_evolution_data()
            record.dashboard_graph = json.dumps(graph_data)

    def _get_cash_evolution_data(self):
        """Obtiene datos de evolución de caja para gráficos"""
        self.ensure_one()
        
        # Obtener movimientos de los últimos 30 días
        end_date = fields.Date.today()
        start_date = end_date - timedelta(days=30)
        
        # Consulta para obtener saldos diarios
        query = """
            SELECT 
                DATE(aml.date) as date,
                SUM(CASE WHEN aj.type = 'cash' THEN aml.balance ELSE 0 END) as cash_balance,
                SUM(CASE WHEN aj.type = 'bank' THEN aml.balance ELSE 0 END) as bank_balance
            FROM account_move_line aml
            JOIN account_account aa ON aml.account_id = aa.id
            JOIN account_journal aj ON aa.id = aj.default_account_id
            WHERE aj.type IN ('cash', 'bank')
                AND aj.company_id = %s
                AND aml.date >= %s
                AND aml.date <= %s
            GROUP BY DATE(aml.date)
            ORDER BY date
        """
        
        self.env.cr.execute(query, (self.company_id.id, start_date, end_date))
        results = self.env.cr.fetchall()
        
        graph_data = {
            'values': [],
            'key': 'Evolución de Caja',
            'title': 'Últimos 30 días'
        }
        
        for date, cash, bank in results:
            graph_data['values'].append({
                'x': date.strftime('%Y-%m-%d'),
                'y': float(cash + bank),
                'cash': float(cash or 0),
                'bank': float(bank or 0)
            })
        
        return [graph_data]

    # ====================================================================
    # MÉTODOS DE ACCIÓN PARA BOTONES DEL DASHBOARD - INCLUYENDO FACTURAS
    # ====================================================================

    def action_view_pending_expenses(self):
        """Acción para ver gastos pendientes"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Gastos Pendientes'),
            'res_model': 'periodic.expense',
            'view_mode': 'list,form',
            'domain': [
                ('company_id', '=', self.company_id.id),
                ('state', '=', 'pending'),
                ('next_payment_date', '<=', fields.Date.today() + timedelta(days=7))
            ],
            'context': {'create': False}
        }

    def action_view_supplier_invoices_not_paid(self):
        """NUEVA ACCIÓN: Ver facturas de proveedores no pagadas"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Facturas de Proveedores - No Pagadas'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [
                ('company_id', '=', self.company_id.id),
                ('move_type', 'in', ['in_invoice', 'in_receipt']),
                ('state', '=', 'posted'),
                ('payment_state', 'in', ['not_paid', 'partial'])
            ],
            'context': {
                'create': False,
                'search_default_not_paid': 1
            }
        }

    def action_view_customer_invoices_not_paid(self):
        """NUEVA ACCIÓN: Ver facturas de clientes no cobradas"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Facturas de Clientes - No Cobradas'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [
                ('company_id', '=', self.company_id.id),
                ('move_type', 'in', ['out_invoice', 'out_receipt']),
                ('state', '=', 'posted'),
                ('payment_state', 'in', ['not_paid', 'partial'])
            ],
            'context': {
                'create': False,
                'search_default_not_paid': 1
            }
        }

    def action_import_invoices_to_cashflow(self):
        """NUEVA ACCIÓN: Importar facturas pendientes al cashflow"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Importar Facturas al Cashflow'),
            'res_model': 'invoice.import.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_company_id': self.company_id.id
            }
        }

    def action_view_cashflow_projection(self):
        """Acción para ver proyección de cashflow"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Proyección de Cashflow'),
            'res_model': 'cashflow.projection',
            'view_mode': 'grid,list,form',
            'domain': [('company_id', '=', self.company_id.id)],
            'context': {
                'default_company_id': self.company_id.id,
                'search_default_current_month': 1
            }
        }

    def action_view_cash_accounts(self):
        """Acción para ver cuentas de caja y banco"""
        self.ensure_one()
        journals = self.env['account.journal'].search([
            ('type', 'in', ['cash', 'bank']),
            ('company_id', '=', self.company_id.id)
        ])
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cuentas de Caja y Bancos'),
            'res_model': 'account.journal',
            'view_mode': 'list,form',
            'domain': [('id', 'in', journals.ids)],
            'context': {'create': False}
        }

    def action_refresh_dashboard(self):
        """Acción para refrescar datos del dashboard manualmente"""
        self.ensure_one()
        # Forzar recálculo de campos computados
        self._compute_totals()
        self._compute_pending_expenses()
        self._compute_invoice_stats()
        self._compute_invoice_amounts()
        self._compute_projections()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Dashboard actualizado exitosamente'),
                'type': 'success'
            }
        }

    # ====================================================================
    # MÉTODOS AUTOMÁTICOS Y CRON JOBS
    # ====================================================================

    @api.model
    def create_dashboard_for_all_companies(self):
        """Método para crear dashboard en todas las compañías que no lo tengan"""
        companies = self.env['res.company'].search([])
        created_count = 0
        
        for company in companies:
            existing = self.search([('company_id', '=', company.id)], limit=1)
            if not existing:
                self.create({'company_id': company.id})
                created_count += 1
        
        return created_count

    @api.model
    def update_all_dashboards(self):
        """Método para actualizar todos los dashboards (para cron job)"""
        dashboards = self.search([])
        for dashboard in dashboards:
            dashboard._compute_totals()
            dashboard._compute_pending_expenses()
            dashboard._compute_invoice_stats()
            dashboard._compute_invoice_amounts()
            dashboard._compute_projections()
        return True