# -*- coding: utf-8 -*-
import json
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class DuxImportBatch(models.Model):
    _name = 'dux.import.batch'
    _description = 'Lote de Datos JSON Dux'
    _order = 'create_date desc, id desc'
    _rec_name = 'batch_name'

    # Información del lote
    batch_name = fields.Char('Nombre del Lote', required=True, index=True)
    connector_id = fields.Many2one('dux.connector', 'Conexión Dux', required=True)
    create_date = fields.Datetime('Fecha Creación', default=fields.Datetime.now, readonly=True)
    
    # Tipo de datos
    data_type = fields.Selection([
        ('ventas', 'Ventas'),
        ('compras', 'Compras'),
        ('pagos', 'Pagos'),
        ('cobros', 'Cobros'),
        ('clientes', 'Clientes'),
        ('productos', 'Productos'),
        ('stock', 'Stock')
    ], string='Tipo de Datos', required=True, index=True)
    
    # Filtros utilizados
    fecha_desde = fields.Date('Fecha Desde')
    fecha_hasta = fields.Date('Fecha Hasta')
    batch_size = fields.Integer('Tamaño de Lote', default=100)
    
    # Datos JSON crudos
    raw_data_json = fields.Text('Datos JSON Crudos', required=True)
    total_records = fields.Integer('Total Registros', compute='_compute_total_records', store=True)
    
    # Estado del lote
    state = fields.Selection([
        ('raw', 'Datos Crudos'),
        ('processing', 'Procesando'),
        ('processed', 'Procesado'),
        ('error', 'Error')
    ], string='Estado', default='raw', index=True)
    
    # Estadísticas de procesamiento
    processed_count = fields.Integer('Registros Procesados', default=0)
    error_count = fields.Integer('Errores', default=0)
    processing_notes = fields.Text('Notas de Procesamiento')
    
    # Relación con registros procesados
    import_record_ids = fields.One2many('dux.import.record', 'batch_id', 'Registros Importados')
    
    @api.depends('raw_data_json')
    def _compute_total_records(self):
        """Calcula total de registros en el JSON"""
        for batch in self:
            try:
                if batch.raw_data_json:
                    data = json.loads(batch.raw_data_json)
                    if isinstance(data, list):
                        batch.total_records = len(data)
                    elif isinstance(data, dict):
                        # Manejar diferentes estructuras de respuesta
                        records = data.get('data', data.get('results', data.get('items', [])))
                        batch.total_records = len(records) if isinstance(records, list) else 1
                    else:
                        batch.total_records = 1
                else:
                    batch.total_records = 0
            except:
                batch.total_records = 0
    
    @api.model
    def generate_batch_name(self, data_type, fecha_desde=None, fecha_hasta=None):
        """Genera nombre del lote según el formato requerido"""
        if fecha_desde and fecha_hasta:
            fecha_desde_str = fecha_desde.strftime('%Y%m%d') if isinstance(fecha_desde, fields.Date) else str(fecha_desde).replace('-', '')
            fecha_hasta_str = fecha_hasta.strftime('%Y%m%d') if isinstance(fecha_hasta, fields.Date) else str(fecha_hasta).replace('-', '')
            return f"{fecha_desde_str}-{fecha_hasta_str} - {data_type.title()}"
        else:
            timestamp = fields.Datetime.now().strftime('%Y%m%d_%H%M')
            return f"{timestamp} - {data_type.title()}"
    
    def action_process_batch(self):
        """Procesa el lote JSON hacia dux.import.record"""
        self.ensure_one()
        
        if self.state != 'raw':
            raise UserError('Solo se pueden procesar lotes en estado "Datos Crudos"')
        
        try:
            self.state = 'processing'
            self.processed_count = 0
            self.error_count = 0
            
            # Parsear JSON
            raw_data = json.loads(self.raw_data_json)
            
            # Normalizar estructura de datos
            if isinstance(raw_data, dict):
                records = raw_data.get('data', raw_data.get('results', raw_data.get('items', [])))
            else:
                records = raw_data
            
            if not isinstance(records, list):
                records = [records]
            
            # Procesar cada registro
            for record_data in records:
                try:
                    self._process_single_record(record_data)
                    self.processed_count += 1
                except Exception as e:
                    self.error_count += 1
                    _logger.error(f"Error procesando registro en lote {self.id}: {str(e)}")
            
            # Actualizar estado final
            if self.error_count == 0:
                self.state = 'processed'
                self.processing_notes = f"Lote procesado exitosamente. {self.processed_count} registros creados."
            else:
                self.state = 'error'
                self.processing_notes = f"Procesamiento completado con errores. {self.processed_count} exitosos, {self.error_count} errores."
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Lote Procesado',
                    'message': self.processing_notes,
                    'type': 'success' if self.error_count == 0 else 'warning',
                }
            }
            
        except Exception as e:
            self.state = 'error'
            self.processing_notes = f"Error fatal procesando lote: {str(e)}"
            _logger.error(f"Error procesando lote {self.id}: {str(e)}")
            raise UserError(f"Error procesando lote: {str(e)}")
    
    def _process_single_record(self, record_data):
        """Procesa un registro individual hacia dux.import.record"""
        if self.data_type == 'ventas':
            return self._process_venta_record(record_data)
        elif self.data_type == 'compras':
            return self._process_compra_record(record_data)
        elif self.data_type == 'pagos':
            return self._process_pago_record(record_data)
        elif self.data_type == 'cobros':
            return self._process_cobro_record(record_data)
        else:
            raise UserError(f"Tipo de datos no soportado: {self.data_type}")
    
    def _process_venta_record(self, dux_venta):
        """Procesa registro de venta hacia dux.import.record"""
        # Extraer datos del cliente
        cliente_nombre = f"{dux_venta.get('apellido_razon_soc', '')} {dux_venta.get('nombre', '')}".strip()
        cliente_cuit = dux_venta.get('cuit', '')
        numero_doc = self._format_dux_number(dux_venta.get('nro_pto_vta', ''), dux_venta.get('nro_comp', ''))
        
        # Buscar partner
        partner = self._find_partner(cliente_cuit, cliente_nombre, dux_venta.get('apellido_razon_soc', ''))
        
        # Procesar detalles
        detalle_lineas = self._process_detail_lines(dux_venta.get('detalles_json', ''))
        detalle_cobros = self._process_detail_cobros(dux_venta.get('detalles_cobro', []))
        
        # Crear registro
        import_record = self.env['dux.import.record'].create({
            'batch_id': self.id,
            'connector_id': self.connector_id.id,
            'dux_id': str(dux_venta.get('id', '')),
            'dux_numero': numero_doc,
            'dux_tipo_comprobante': dux_venta.get('tipo_comp', ''),
            'dux_data_json': json.dumps(dux_venta),
            'tipo': 'venta',
            'partner_id': partner.id if partner else False,
            'date': self._parse_dux_date(dux_venta.get('fecha_comp')),
            'amount_total': float(dux_venta.get('total', 0)),
            'detalle_lineas': detalle_lineas,
            'detalle_cobros': detalle_cobros,
            'state': 'imported'
        })
        
        return import_record
    
    def _process_compra_record(self, dux_compra):
        """Procesa registro de compra hacia dux.import.record"""
        # Implementar lógica similar para compras
        proveedor = dux_compra.get('proveedor', {})
        
        import_record = self.env['dux.import.record'].create({
            'batch_id': self.id,
            'connector_id': self.connector_id.id,
            'dux_id': str(dux_compra.get('id', '')),
            'dux_numero': dux_compra.get('numero', ''),
            'dux_tipo_comprobante': dux_compra.get('tipoComprobante', ''),
            'dux_data_json': json.dumps(dux_compra),
            'tipo': 'compra',
            'partner_id': self._find_partner_by_cuit(proveedor.get('cuit', '')).id if self._find_partner_by_cuit(proveedor.get('cuit', '')) else False,
            'date': self._parse_dux_date(dux_compra.get('fecha')),
            'amount_total': float(dux_compra.get('total', 0)),
            'state': 'imported'
        })
        
        return import_record
    
    def _process_pago_record(self, dux_pago):
        """Procesa registro de pago hacia dux.import.record"""
        proveedor = dux_pago.get('proveedor', {})
        
        import_record = self.env['dux.import.record'].create({
            'batch_id': self.id,
            'connector_id': self.connector_id.id,
            'dux_id': str(dux_pago.get('id', '')),
            'dux_numero': dux_pago.get('numero', ''),
            'dux_tipo_comprobante': 'Pago',
            'dux_data_json': json.dumps(dux_pago),
            'tipo': 'pago',
            'partner_id': self._find_partner_by_cuit(proveedor.get('cuit', '')).id if self._find_partner_by_cuit(proveedor.get('cuit', '')) else False,
            'date': self._parse_dux_date(dux_pago.get('fecha')),
            'amount_total': float(dux_pago.get('importe', 0)),
            'state': 'imported'
        })
        
        return import_record
    
    def _process_cobro_record(self, dux_cobro):
        """Procesa registro de cobro hacia dux.import.record"""
        cliente = dux_cobro.get('cliente', {})
        
        import_record = self.env['dux.import.record'].create({
            'batch_id': self.id,
            'connector_id': self.connector_id.id,
            'dux_id': str(dux_cobro.get('id', '')),
            'dux_numero': dux_cobro.get('numero', ''),
            'dux_tipo_comprobante': 'Cobro',
            'dux_data_json': json.dumps(dux_cobro),
            'tipo': 'cobro',
            'partner_id': self._find_partner_by_cuit(cliente.get('cuit', '')).id if self._find_partner_by_cuit(cliente.get('cuit', '')) else False,
            'date': self._parse_dux_date(dux_cobro.get('fecha')),
            'amount_total': float(dux_cobro.get('importe', 0)),
            'state': 'imported'
        })
        
        return import_record
    
    # Métodos auxiliares reutilizados del wizard original
    def _format_dux_number(self, nro_pto_vta, nro_comp):
        """Formatea número Dux como 00010-00000045"""
        try:
            pto_vta = str(nro_pto_vta).zfill(5)
            comp = str(nro_comp).zfill(8)
            return f"{pto_vta}-{comp}"
        except:
            return f"{nro_pto_vta}-{nro_comp}"
    
    def _find_partner(self, cuit, nombre_completo, apellido_razon_soc):
        """Busca partner con prioridad: 1º CUIT, 2º nombre completo, 3º apellido+CUIT, 4º apellido"""
        partner = False
        
        if cuit:
            partner = self.env['res.partner'].search([('vat', '=', cuit)], limit=1)
            if partner:
                return partner
        
        if nombre_completo:
            partner = self.env['res.partner'].search([('name', 'ilike', nombre_completo)], limit=1)
            if partner:
                return partner
        
        if apellido_razon_soc and cuit:
            partner = self.env['res.partner'].search([
                ('name', 'ilike', apellido_razon_soc),
                ('vat', '=', cuit)
            ], limit=1)
            if partner:
                return partner
        
        if apellido_razon_soc:
            partner = self.env['res.partner'].search([('name', 'ilike', apellido_razon_soc)], limit=1)
            if partner:
                return partner
        
        return False
    
    def _find_partner_by_cuit(self, cuit):
        """Busca partner por CUIT"""
        if cuit:
            return self.env['res.partner'].search([('vat', '=', cuit)], limit=1)
        return False
    
    def _process_detail_lines(self, detalles_json):
        """Procesa detalles JSON y retorna formato estructurado"""
        if not detalles_json:
            return ""
        
        try:
            detalles = json.loads(detalles_json)
            lineas = []
            
            for detalle in detalles:
                cod_item = detalle.get('cod_item', '')
                item = detalle.get('item', '')
                cantidad = detalle.get('ctd', 0)
                precio_uni = detalle.get('precio_uni', 0)
                
                linea = f"[{cod_item}] - [{item}] - [cantidad: {cantidad}] - [{precio_uni}]"
                lineas.append(linea)
            
            return "\n".join(lineas)
            
        except Exception as e:
            return f"Error procesando detalles: {str(e)}"
    
    def _process_detail_cobros(self, detalles_cobro):
        """Procesa detalles de cobro y retorna formato estructurado"""
        if not detalles_cobro:
            return ""
        
        try:
            lineas = []
            
            for cobro in detalles_cobro:
                punto_venta = cobro.get('numero_punto_de_venta', '')
                comprobante = cobro.get('numero_comprobante', '')
                personal = cobro.get('personal', '')
                caja = cobro.get('caja', '')
                
                movimientos = cobro.get('detalles_mov_cobro', [])
                for mov in movimientos:
                    tipo_valor = mov.get('tipo_de_valor', '')
                    referencia = mov.get('referencia', '')
                    monto = mov.get('monto', 0)
                    
                    linea = f"PV:{punto_venta} - Comp:{comprobante} - {personal} - {caja} - {tipo_valor} - ${monto}"
                    if referencia:
                        linea += f" - Ref: {referencia}"
                    lineas.append(linea)
            
            return "\n".join(lineas)
            
        except Exception as e:
            return f"Error procesando cobros: {str(e)}"
    
    def _parse_dux_date(self, date_str):
        """Convierte fecha de Dux a date"""
        if not date_str:
            return fields.Date.today()
        
        try:
            from datetime import datetime
            if 'AM' in str(date_str) or 'PM' in str(date_str):
                date_part = str(date_str).split(' ')[:3]
                date_clean = ' '.join(date_part)
                dt = datetime.strptime(date_clean, '%b %d, %Y')
                return dt.date()
            
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']:
                try:
                    dt = datetime.strptime(str(date_str).split(' ')[0], fmt)
                    return dt.date()
                except ValueError:
                    continue
            return fields.Date.today()
        except:
            return fields.Date.today()
    
    def action_view_import_records(self):
        """Abre vista de registros importados del lote"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Registros - {self.batch_name}',
            'res_model': 'dux.import.record',
            'view_mode': 'tree,form',
            'domain': [('batch_id', '=', self.id)],
            'context': {'default_batch_id': self.id}
        }