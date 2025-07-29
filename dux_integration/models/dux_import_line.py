# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class DuxImportLine(models.TransientModel):
    _name = 'dux.import.line'
    _description = 'Línea de Importación Dux'
    _order = 'sequence, id'

    wizard_id = fields.Many2one('dux.import.wizard', 'Wizard', ondelete='cascade')
    sequence = fields.Integer('Secuencia', default=10)
    
    # Datos de origen
    tipo = fields.Selection([
        ('venta', 'Venta'),
        ('compra', 'Compra'),
        ('pago', 'Pago'),
        ('cobro', 'Cobro')
    ], string='Tipo', required=True)
    
    dux_id = fields.Char('ID Dux', required=True)
    dux_numero = fields.Char('Número Dux')
    dux_tipo_comprobante = fields.Char('Tipo Comprobante Dux')
    
    # Datos mapeados
    partner_id = fields.Many2one('res.partner', 'Cliente/Proveedor')
    partner_name = fields.Char('Nombre Cliente/Proveedor')
    partner_vat = fields.Char('CUIT/DNI')
    
    journal_id = fields.Many2one('account.journal', 'Diario')
    journal_suggested = fields.Char('Diario Sugerido', readonly=True)
    
    date = fields.Date('Fecha')
    amount_total = fields.Float('Total')
    currency_id = fields.Many2one('res.currency', 'Moneda', 
                                 default=lambda self: self.env.company.currency_id)
    
    # Estado y validación
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('validated', 'Validado'),
        ('imported', 'Importado'),
        ('error', 'Error')
    ], string='Estado', default='draft')
    
    error_msg = fields.Text('Error')
    warning_msg = fields.Text('Advertencias')
    
    # Datos JSON originales
    dux_data = fields.Text('Datos Dux (JSON)')
    
    # Campos calculados
    move_type = fields.Selection([
        ('out_invoice', 'Factura Cliente'),
        ('out_refund', 'Nota Crédito Cliente'),
        ('in_invoice', 'Factura Proveedor'),
        ('in_refund', 'Nota Crédito Proveedor'),
        ('entry', 'Asiento Contable')
    ], compute='_compute_move_type', store=True)
    
    @api.depends('tipo', 'dux_tipo_comprobante')
    def _compute_move_type(self):
        """Calcula el tipo de movimiento contable"""
        for line in self:
            if line.tipo == 'venta':
                line.move_type = 'out_invoice'
            elif line.tipo == 'compra':
                line.move_type = 'in_invoice'
            else:
                line.move_type = 'entry'
    
    def action_validate(self):
        """Valida la línea antes de importar"""
        for line in self:
            errors = []
            warnings = []
            
            # Validar partner
            if not line.partner_id:
                if line.partner_vat:
                    partner = self.env['res.partner'].search([
                        ('vat', '=', line.partner_vat)
                    ], limit=1)
                    if partner:
                        line.partner_id = partner.id
                        warnings.append(f'Partner encontrado por CUIT: {partner.name}')
                    else:
                        errors.append(f'Partner no encontrado con CUIT: {line.partner_vat}')
                else:
                    errors.append('Partner requerido')
            
            # Validar diario
            if not line.journal_id:
                journal = line._suggest_journal()
                if journal:
                    line.journal_id = journal.id
                    warnings.append(f'Diario sugerido: {journal.name}')
                else:
                    errors.append('No se pudo determinar el diario')
            
            # Validar datos obligatorios
            if not line.date:
                errors.append('Fecha requerida')
            if not line.amount_total:
                errors.append('Monto requerido')
            
            # Actualizar estado
            if errors:
                line.state = 'error'
                line.error_msg = '\n'.join(errors)
            else:
                line.state = 'validated'
                line.error_msg = False
            
            if warnings:
                line.warning_msg = '\n'.join(warnings)
    
    def _suggest_journal(self):
        """Sugiere un diario basado en el tipo de comprobante Dux"""
        mapper = self.env['dux.journal.mapper']
        return mapper.get_journal_for_dux_type(self.dux_tipo_comprobante, self.tipo)
    
    def action_import(self):
        """Importa la línea a Odoo"""
        for line in self:
            if line.state != 'validated':
                raise UserError(f'La línea {line.dux_numero} debe estar validada')
            
            try:
                if line.tipo in ['venta', 'compra']:
                    move = line._create_account_move()
                    line.state = 'imported'
                    _logger.info(f'Importado: {move.name}')
                elif line.tipo in ['pago', 'cobro']:
                    payment = line._create_payment()
                    line.state = 'imported'
                    _logger.info(f'Pago importado: {payment.name}')
                    
            except Exception as e:
                line.state = 'error'
                line.error_msg = str(e)
                _logger.error(f'Error importando línea {line.id}: {str(e)}')
    
    def _create_account_move(self):
        """Crea un account.move"""
        # Extraer ID sucursal de los datos JSON
        dux_data = eval(self.dux_data) if self.dux_data else {}
        sucursal_info = ""
        if dux_data.get('sucursal'):
            sucursal_info = f"\nSucursal: {dux_data['sucursal']}"
        
        move_vals = {
            'move_type': self.move_type,
            'partner_id': self.partner_id.id,
            'invoice_date': self.date,
            'date': self.date,
            'journal_id': self.journal_id.id,
            'ref': f'Dux-{self.dux_numero}',
            'narration': f'Importado desde Dux ID: {self.dux_id}{sucursal_info}',
            'invoice_line_ids': [(0, 0, {
                'name': f'Importación Dux {self.dux_numero}',
                'quantity': 1,
                'price_unit': self.amount_total,
                'account_id': self._get_default_account().id,
            })]
        }
        
        return self.env['account.move'].create(move_vals)
    
    def _create_payment(self):
        """Crea un account.payment"""
        payment_type = 'inbound' if self.tipo == 'cobro' else 'outbound'
        partner_type = 'customer' if self.tipo == 'cobro' else 'supplier'
        
        # Extraer sucursal
        dux_data = eval(self.dux_data) if self.dux_data else {}
        sucursal_info = ""
        if dux_data.get('sucursal'):
            sucursal_info = f" - Sucursal: {dux_data['sucursal']}"
        
        payment_vals = {
            'payment_type': payment_type,
            'partner_type': partner_type,
            'partner_id': self.partner_id.id,
            'amount': self.amount_total,
            'date': self.date,
            'journal_id': self.journal_id.id,
            'ref': f'Dux-{self.dux_numero}{sucursal_info}',
        }
        
        return self.env['account.payment'].create(payment_vals)
    
    def _get_default_account(self):
        """Obtiene cuenta contable por defecto"""
        if self.tipo == 'venta':
            return self.env['account.account'].search([
                ('account_type', '=', 'income')
            ], limit=1)
        else:
            return self.env['account.account'].search([
                ('account_type', '=', 'expense')
            ], limit=1)

class DuxJournalMapper(models.Model):
    _name = 'dux.journal.mapper'
    _description = 'Mapeo de Diarios Dux a Odoo'
    
    name = fields.Char('Nombre', required=True)
    dux_type = fields.Char('Tipo Comprobante Dux', required=True)
    operation_type = fields.Selection([
        ('venta', 'Venta'),
        ('compra', 'Compra'),
        ('pago', 'Pago'),
        ('cobro', 'Cobro')
    ], required=True)
    
    journal_id = fields.Many2one('account.journal', 'Diario Odoo', required=True)
    active = fields.Boolean('Activo', default=True)
    
    def get_journal_for_dux_type(self, dux_type, operation_type):
        """Obtiene el diario correspondiente"""
        mapper = self.search([
            ('dux_type', '=', dux_type),
            ('operation_type', '=', operation_type),
            ('active', '=', True)
        ], limit=1)
        
        if mapper:
            return mapper.journal_id
        
        # Mapeo por defecto si no existe configuración
        return self._get_default_journal(operation_type)
    
    def _get_default_journal(self, operation_type):
        """Obtiene diario por defecto según operación"""
        if operation_type == 'venta':
            return self.env['account.journal'].search([
                ('type', '=', 'sale')
            ], limit=1)
        elif operation_type == 'compra':
            return self.env['account.journal'].search([
                ('type', '=', 'purchase')
            ], limit=1)
        else:
            return self.env['account.journal'].search([
                ('type', '=', 'bank')
            ], limit=1)