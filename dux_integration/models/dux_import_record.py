# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class DuxImportRecord(models.Model):
    _name = 'dux.import.record'
    _description = 'Registro de Importación Dux'
    _order = 'import_date desc, id desc'
    _rec_name = 'display_name'

    # Información de importación
    import_date = fields.Datetime('Fecha Importación', default=fields.Datetime.now)
    connector_id = fields.Many2one('dux.connector', 'Conexión Dux')
    import_batch = fields.Char('Lote Importación', default=lambda self: self._generate_batch())
    
    # Datos originales de Dux
    dux_id = fields.Char('ID Dux', required=True, index=True)
    dux_numero = fields.Char('Número Dux')
    dux_tipo_comprobante = fields.Char('Tipo Comprobante Dux')
    dux_data_json = fields.Text('Datos JSON Originales')
    
    # Tipo y estado
    tipo = fields.Selection([
        ('venta', 'Venta'),
        ('compra', 'Compra'),
        ('pago', 'Pago'),
        ('cobro', 'Cobro')
    ], required=True, index=True)
    
    state = fields.Selection([
        ('imported', 'Importado'),
        ('processed', 'Procesado'),
        ('error', 'Error')
    ], default='imported', index=True)
    
    # Datos mapeados
    partner_id = fields.Many2one('res.partner', 'Cliente/Proveedor')
    journal_id = fields.Many2one('account.journal', 'Diario')
    date = fields.Date('Fecha Documento')
    amount_total = fields.Float('Total')
    
    # Referencias Odoo creadas
    move_id = fields.Many2one('account.move', 'Asiento Contable')
    payment_id = fields.Many2one('account.payment', 'Pago')
    
    # Información adicional
    notes = fields.Text('Notas')
    error_msg = fields.Text('Mensaje Error')
    detalle_lineas = fields.Text('Detalle Líneas Pedido')
    
    display_name = fields.Char('Nombre', compute='_compute_display_name', store=True)
    
    @api.depends('tipo', 'dux_numero', 'partner_id')
    def _compute_display_name(self):
        for record in self:
            partner_name = record.partner_id.name if record.partner_id else 'Sin partner'
            record.display_name = f"{record.tipo.title()} {record.dux_numero} - {partner_name}"
    
    @api.model
    def _generate_batch(self):
        """Genera código único para lote de importación"""
        return fields.Datetime.now().strftime('DUX_%Y%m%d_%H%M%S')
    
    def action_process_record(self):
        """Procesa el registro importado"""
        for record in self:
            if record.state != 'imported':
                continue
                
            try:
                if record.tipo in ['venta', 'compra']:
                    move = record._create_account_move()
                    record.move_id = move.id
                elif record.tipo in ['pago', 'cobro']:
                    payment = record._create_payment()
                    record.payment_id = payment.id
                
                record.state = 'processed'
                
            except Exception as e:
                record.state = 'error'
                record.error_msg = str(e)
    
    def _create_account_move(self):
        """Crea account.move desde registro importado"""
        move_type = 'out_invoice' if self.tipo == 'venta' else 'in_invoice'
        
        dux_data = eval(self.dux_data_json) if self.dux_data_json else {}
        sucursal_info = f"\nSucursal: {dux_data.get('sucursal', '')}" if dux_data.get('sucursal') else ""
        
        # Procesar líneas de factura
        invoice_lines = self._create_invoice_lines(dux_data)
        
        move_vals = {
            'move_type': move_type,
            'partner_id': self.partner_id.id,
            'invoice_date': self.date,
            'date': self.date,
            'journal_id': self.journal_id.id,
            'ref': f'Dux-{self.dux_numero}',
            'narration': f'Importado desde Dux ID: {self.dux_id}{sucursal_info}',
            'invoice_line_ids': invoice_lines
        }
        
        return self.env['account.move'].create(move_vals)
    
    def _create_invoice_lines(self, dux_data):
        """Crea líneas de factura desde datos Dux"""
        lines = []
        detalles_json = dux_data.get('detalles_json', '[]')
        
        try:
            import json
            detalles = json.loads(detalles_json)
            
            for detalle in detalles:
                cod_item = detalle.get('cod_item', '')
                item_desc = detalle.get('item', '')
                comentarios = detalle.get('comentarios', '')
                cantidad = float(detalle.get('ctd', 1))
                precio_uni = float(detalle.get('precio_uni', 0))
                porc_iva = float(detalle.get('porc_iva', 0))
                
                # Buscar producto por código
                product = self.env['product.product'].search([
                    ('default_code', '=', cod_item)
                ], limit=1)
                
                # Nombre de línea
                line_name = f"{cod_item} - {item_desc}"
                if comentarios:
                    line_name += f" - {comentarios}"
                
                # Configurar impuesto
                tax_ids = []
                if porc_iva > 0:
                    tax = self.env['account.tax'].search([
                        ('name', 'ilike', f'IVA {int(porc_iva)}%'),
                        ('type_tax_use', '=', 'sale' if self.tipo == 'venta' else 'purchase')
                    ], limit=1)
                    if tax:
                        tax_ids = [(6, 0, [tax.id])]
                
                line_vals = {
                    'product_id': product.id if product else False,
                    'name': line_name,
                    'quantity': round(cantidad, 2),
                    'price_unit': precio_uni,
                    'tax_ids': tax_ids,
                    'account_id': self._get_line_account(product).id,
                }
                
                lines.append((0, 0, line_vals))
                
        except Exception as e:
            # Línea simple si falla el procesamiento
            lines.append((0, 0, {
                'name': f'Importación Dux {self.dux_numero}',
                'quantity': 1,
                'price_unit': self.amount_total,
                'account_id': self._get_default_account().id,
            }))
        
        return lines
    
    def _get_line_account(self, product):
        """Obtiene cuenta contable para línea"""
        if product:
            if self.tipo == 'venta':
                return product.property_account_income_id or product.categ_id.property_account_income_categ_id
            else:
                return product.property_account_expense_id or product.categ_id.property_account_expense_categ_id
        
        return self._get_default_account()
    
    def _create_payment(self):
        """Crea account.payment desde registro importado"""
        payment_type = 'inbound' if self.tipo == 'cobro' else 'outbound'
        partner_type = 'customer' if self.tipo == 'cobro' else 'supplier'
        
        dux_data = eval(self.dux_data_json) if self.dux_data_json else {}
        sucursal_info = f" - Sucursal: {dux_data.get('sucursal', '')}" if dux_data.get('sucursal') else ""
        
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
    
    def action_view_document(self):
        """Abre documento contable generado"""
        if self.move_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'res_id': self.move_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
        elif self.payment_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'account.payment',
                'res_id': self.payment_id.id,
                'view_mode': 'form',
                'target': 'current',
            }