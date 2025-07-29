# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class DuxImportWizard(models.TransientModel):
    _name = 'dux.import.wizard'
    _description = 'Asistente de Importación Dux'

    # Configuración general
    connector_id = fields.Many2one('dux.connector', 'Conexión Dux', required=True,
                                  default=lambda self: self.env['dux.connector'].get_default_connector())
    import_mode = fields.Selection([
        ('test', 'Modo Prueba (solo validar)'),
        ('import', 'Importar Datos')
    ], string='Modo', default='test', required=True)
    
    # Selección de datos a importar
    import_clientes = fields.Boolean('Importar Clientes', default=True)
    import_productos = fields.Boolean('Importar Productos', default=True)
    import_ventas = fields.Boolean('Importar Ventas', default=False)
    import_compras = fields.Boolean('Importar Compras', default=False)
    import_pagos = fields.Boolean('Importar Pagos', default=False)
    import_cobros = fields.Boolean('Importar Cobros', default=False)
    import_stock = fields.Boolean('Actualizar Stock', default=False)
    
    # Opciones de importación
    batch_size = fields.Integer('Tamaño de Lote', default=100, 
                               help='Cantidad de registros a procesar por lote')
    update_existing = fields.Boolean('Actualizar Existentes', default=True,
                                   help='Si está marcado, actualiza registros existentes')
    
    # Filtros de fecha para ventas/compras
    fecha_desde = fields.Date('Fecha Desde')
    fecha_hasta = fields.Date('Fecha Hasta')
    
    # Resultados
    log_ids = fields.One2many('dux.import.log', 'wizard_id', 'Logs')
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('running', 'Ejecutando'),
        ('done', 'Completado'),
        ('error', 'Error')
    ], default='draft')
    
    # Estadísticas
    total_processed = fields.Integer('Total Procesados', readonly=True)
    total_created = fields.Integer('Total Creados', readonly=True)
    total_updated = fields.Integer('Total Actualizados', readonly=True)
    total_errors = fields.Integer('Total Errores', readonly=True)

    # Líneas de importación
    line_ids = fields.One2many('dux.import.line', 'wizard_id', 'Líneas de Importación')
    
    # Estado de proceso
    current_step = fields.Selection([
        ('config', 'Configuración'),
        ('preview', 'Vista Previa'),
        ('import', 'Importación')
    ], default='config', required=True)
    
    def action_import(self):
        """Paso 1: Cargar datos en tabla intermedia"""
        self.ensure_one()
        
        try:
            self.state = 'running'
            self._clear_logs()
            self._clear_lines()
            
            # Verificar conexión
            self.connector_id.test_connection()
            
            # Cargar datos en tabla intermedia
            if self.import_clientes:
                self._load_clientes_preview()
            
            if self.import_productos:
                self._load_productos_preview()
                
            if self.import_ventas:
                self._load_ventas_preview()
                
            if self.import_compras:
                self._load_compras_preview()
            
            if self.import_pagos:
                self._load_pagos_preview()
            
            if self.import_cobros:
                self._load_cobros_preview()
            
            self.current_step = 'preview'
            self.state = 'done'
            self._log('info', 'Datos cargados en vista previa')
            
            return self._show_preview()
            
        except Exception as e:
            self.state = 'error'
            self._log('error', f'Error cargando datos: {str(e)}')
            raise UserError(f"Error: {str(e)}")

    def action_validate_all(self):
        """Valida todas las líneas"""
        self.line_ids.action_validate()
        self._log('info', f'Validadas {len(self.line_ids)} líneas')
    
    def action_import_validated(self):
        """Importa solo líneas validadas"""
        validated_lines = self.line_ids.filtered(lambda l: l.state == 'validated')
        if not validated_lines:
            raise UserError('No hay líneas validadas para importar')
        
        validated_lines.action_import()
        self.current_step = 'import'
        
        imported = len(validated_lines.filtered(lambda l: l.state == 'imported'))
        self._log('info', f'Importadas {imported} líneas exitosamente')
    
    def _load_ventas_preview(self):
        """Carga ventas en vista previa"""
        self._log('info', 'Cargando ventas...')
        
        offset = 0
        
        while True:
            try:
                response = self.connector_id.get_ventas(
                    fecha_desde=self.fecha_desde,
                    fecha_hasta=self.fecha_hasta,
                    limit=self.batch_size,
                    offset=offset
                )
                
                # DEBUG: Logear la respuesta completa
                self._log('info', f'Respuesta API ventas: {str(response)[:500]}...')
                
                # Manejar diferentes estructuras de respuesta
                if isinstance(response, dict):
                    ventas = response.get('data', response.get('results', response.get('items', [])))
                elif isinstance(response, list):
                    ventas = response
                else:
                    ventas = []
                
                self._log('info', f'Ventas encontradas: {len(ventas)}')
                
                if not ventas:
                    break
                
                for i, venta in enumerate(ventas):
                    try:
                        self._log('info', f'Procesando venta {i+1}: {str(venta)[:200]}...')
                        self._create_venta_line(venta)
                        self.total_processed += 1
                    except Exception as e:
                        self.total_errors += 1
                        self._log('error', f'Error procesando venta {i+1}: {str(e)}')
                
                offset += self.batch_size
                if len(ventas) < self.batch_size:
                    break
                    
            except Exception as e:
                self._log('error', f'Error cargando ventas: {str(e)}')
                break
    
    def _create_venta_line(self, dux_venta):
        """Crea línea de venta en tabla intermedia Y permanente"""
        try:
            # Crear en tabla PERMANENTE
            import_record = self.env['dux.import.record'].create({
                'connector_id': self.connector_id.id,
                'dux_id': str(dux_venta.get('id', '')),
                'dux_numero': dux_venta.get('numero', ''),
                'dux_tipo_comprobante': dux_venta.get('tipoComprobante', ''),
                'dux_data_json': str(dux_venta),
                'tipo': 'venta',
                'date': self._parse_dux_date(dux_venta.get('fecha')),
                'amount_total': float(dux_venta.get('total', 0)),
                'state': 'imported'
            })
            
            # Crear en tabla temporal para vista previa
            tipo_comp = dux_venta.get('tipoComprobante', '')
            journal_suggested = self._map_dux_type_to_journal(tipo_comp, 'venta')
            
            line_vals = {
                'wizard_id': self.id,
                'tipo': 'venta',
                'dux_id': str(dux_venta.get('id', '')),
                'dux_numero': dux_venta.get('numero', ''),
                'dux_tipo_comprobante': tipo_comp,
                'partner_name': dux_venta.get('cliente', {}).get('razonSocial', ''),
                'partner_vat': dux_venta.get('cliente', {}).get('cuit', ''),
                'date': self._parse_dux_date(dux_venta.get('fecha')),
                'amount_total': float(dux_venta.get('total', 0)),
                'journal_suggested': journal_suggested,
                'dux_data': str(dux_venta),
                'state': 'draft'
            }
            
            self.env['dux.import.line'].create(line_vals)
            
        except Exception as e:
            self._log('error', f'Error creando línea venta {dux_venta.get("id")}: {str(e)}')
    
    def _load_compras_preview(self):
        """Carga compras en vista previa"""
        self._log('info', 'Cargando compras...')
        
        offset = 0
        while True:
            try:
                response = self.connector_id.get_compras(
                    fecha_desde=self.fecha_desde,
                    fecha_hasta=self.fecha_hasta,
                    limit=self.batch_size,
                    offset=offset
                )
                
                compras = response.get('data', []) if isinstance(response, dict) else response
                if not compras:
                    break
                
                for compra in compras:
                    self._create_compra_line(compra)
                    self.total_processed += 1
                
                offset += self.batch_size
                if len(compras) < self.batch_size:
                    break
                    
            except Exception as e:
                self._log('error', f'Error cargando compras: {str(e)}')
                break
    
    def _create_compra_line(self, dux_compra):
        """Crea línea de compra en tabla intermedia"""
        try:
            tipo_comp = dux_compra.get('tipoComprobante', '')
            journal_suggested = self._map_dux_type_to_journal(tipo_comp, 'compra')
            
            line_vals = {
                'wizard_id': self.id,
                'tipo': 'compra',
                'dux_id': str(dux_compra.get('id', '')),
                'dux_numero': dux_compra.get('numero', ''),
                'dux_tipo_comprobante': tipo_comp,
                'partner_name': dux_compra.get('proveedor', {}).get('razonSocial', ''),
                'partner_vat': dux_compra.get('proveedor', {}).get('cuit', ''),
                'date': self._parse_dux_date(dux_compra.get('fecha')),
                'amount_total': float(dux_compra.get('total', 0)),
                'journal_suggested': journal_suggested,
                'dux_data': str(dux_compra),
                'state': 'draft'
            }
            
            self.env['dux.import.line'].create(line_vals)
            
        except Exception as e:
            self._log('error', f'Error creando línea compra {dux_compra.get("id")}: {str(e)}')
    
    def _load_pagos_preview(self):
        """Carga pagos en vista previa"""
        self._log('info', 'Cargando pagos...')
        
        offset = 0
        while True:
            try:
                response = self.connector_id.get_pagos(
                    fecha_desde=self.fecha_desde,
                    fecha_hasta=self.fecha_hasta,
                    limit=self.batch_size,
                    offset=offset
                )
                
                pagos = response.get('data', []) if isinstance(response, dict) else response
                if not pagos:
                    break
                
                for pago in pagos:
                    self._create_pago_line(pago)
                    self.total_processed += 1
                
                offset += self.batch_size
                if len(pagos) < self.batch_size:
                    break
                    
            except Exception as e:
                self._log('error', f'Error cargando pagos: {str(e)}')
                break
    
    def _create_pago_line(self, dux_pago):
        """Crea línea de pago en tabla intermedia"""
        try:
            line_vals = {
                'wizard_id': self.id,
                'tipo': 'pago',
                'dux_id': str(dux_pago.get('id', '')),
                'dux_numero': dux_pago.get('numero', ''),
                'dux_tipo_comprobante': 'Pago',
                'partner_name': dux_pago.get('proveedor', {}).get('razonSocial', ''),
                'partner_vat': dux_pago.get('proveedor', {}).get('cuit', ''),
                'date': self._parse_dux_date(dux_pago.get('fecha')),
                'amount_total': float(dux_pago.get('importe', 0)),
                'journal_suggested': 'Banco',
                'dux_data': str(dux_pago),
                'state': 'draft'
            }
            
            self.env['dux.import.line'].create(line_vals)
            
        except Exception as e:
            self._log('error', f'Error creando línea pago {dux_pago.get("id")}: {str(e)}')
    
    def _load_cobros_preview(self):
        """Carga cobros en vista previa"""
        self._log('info', 'Cargando cobros...')
        
        offset = 0
        while True:
            try:
                response = self.connector_id.get_cobros(
                    fecha_desde=self.fecha_desde,
                    fecha_hasta=self.fecha_hasta,
                    limit=self.batch_size,
                    offset=offset
                )
                
                cobros = response.get('data', []) if isinstance(response, dict) else response
                if not cobros:
                    break
                
                for cobro in cobros:
                    self._create_cobro_line(cobro)
                    self.total_processed += 1
                
                offset += self.batch_size
                if len(cobros) < self.batch_size:
                    break
                    
            except Exception as e:
                self._log('error', f'Error cargando cobros: {str(e)}')
                break
    
    def _create_cobro_line(self, dux_cobro):
        """Crea línea de cobro en tabla intermedia"""
        try:
            line_vals = {
                'wizard_id': self.id,
                'tipo': 'cobro',
                'dux_id': str(dux_cobro.get('id', '')),
                'dux_numero': dux_cobro.get('numero', ''),
                'dux_tipo_comprobante': 'Cobro',
                'partner_name': dux_cobro.get('cliente', {}).get('razonSocial', ''),
                'partner_vat': dux_cobro.get('cliente', {}).get('cuit', ''),
                'date': self._parse_dux_date(dux_cobro.get('fecha')),
                'amount_total': float(dux_cobro.get('importe', 0)),
                'journal_suggested': 'Banco',
                'dux_data': str(dux_cobro),
                'state': 'draft'
            }
            
            self.env['dux.import.line'].create(line_vals)
            
        except Exception as e:
            self._log('error', f'Error creando línea cobro {dux_cobro.get("id")}: {str(e)}')
    
    def _map_dux_type_to_journal(self, dux_type, operation_type):
        """Mapea tipo Dux a nombre de diario sugerido"""
        mapping = {
            'venta': {
                'Comprobante de Venta': 'Comprobante de Venta',
                'Factura': 'Facturas de Ventas',
                'Factura de Crédito Electronica MiPymes': 'Facturas de Ventas'
            },
            'compra': {
                'Comprobante de Compra': 'Comprobantes de Compra',
                'Factura': 'Facturas de Proveedores FISCAL'
            }
        }
        
        return mapping.get(operation_type, {}).get(dux_type, 'Sin mapear')
    
    def _parse_dux_date(self, date_str):
        """Convierte fecha de Dux a date"""
        if not date_str:
            return fields.Date.today()
        
        try:
            from datetime import datetime
            # Probar formatos comunes
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']:
                try:
                    dt = datetime.strptime(str(date_str).split(' ')[0], fmt)
                    return dt.date()
                except ValueError:
                    continue
            return fields.Date.today()
        except:
            return fields.Date.today()
    
    def _clear_lines(self):
        """Limpia líneas anteriores"""
        self.line_ids.unlink()
    
    def _show_preview(self):
        """Muestra vista previa de datos"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Vista Previa Importación',
            'res_model': 'dux.import.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'show_preview': True}
        }

    def _import_clientes(self):
        """Importa clientes desde Dux"""
        self._log('info', 'Iniciando importación de clientes...')
        
        offset = 0
        mapper = self.env['dux.data.mapper']
        
        while True:
            try:
                # Obtener lote de clientes
                response = self.connector_id.get_clientes(
                    limit=self.batch_size, 
                    offset=offset
                )
                
                clientes = response.get('data', [])
                if not clientes:
                    break
                
                for cliente in clientes:
                    try:
                        self._process_cliente(cliente, mapper)
                        self.total_processed += 1
                        
                    except Exception as e:
                        self.total_errors += 1
                        self._log('error', f'Error procesando cliente {cliente.get("id")}: {str(e)}')
                
                offset += self.batch_size
                
                # Evitar bucle infinito
                if len(clientes) < self.batch_size:
                    break
                    
            except Exception as e:
                self._log('error', f'Error obteniendo clientes (offset {offset}): {str(e)}')
                break
        
        self._log('info', f'Clientes procesados: {self.total_processed}')

    def _process_cliente(self, dux_cliente, mapper):
        """Procesa un cliente individual"""
        # Mapear datos
        partner_data = mapper.map_cliente_to_partner(dux_cliente)
        
        if self.import_mode == 'test':
            self._log('info', f'[TEST] Cliente: {partner_data.get("name")} - {partner_data.get("vat")}')
            return
        
        # Buscar cliente existente
        existing = None
        if dux_cliente.get('cuit'):
            existing = self.env['res.partner'].search([
                ('vat', '=', dux_cliente['cuit'])
            ], limit=1)
        
        if existing and self.update_existing:
            existing.write(partner_data)
            self.total_updated += 1
            self._log('info', f'Cliente actualizado: {partner_data["name"]}')
        elif not existing:
            partner = self.env['res.partner'].create(partner_data)
            self.total_created += 1
            self._log('info', f'Cliente creado: {partner.name}')

    def _import_productos(self):
        """Importa productos desde Dux"""
        self._log('info', 'Iniciando importación de productos...')
        
        offset = 0
        mapper = self.env['dux.data.mapper']
        
        while True:
            try:
                response = self.connector_id.get_productos(
                    limit=self.batch_size,
                    offset=offset
                )
                
                productos = response.get('data', [])
                if not productos:
                    break
                
                for producto in productos:
                    try:
                        self._process_producto(producto, mapper)
                        self.total_processed += 1
                        
                    except Exception as e:
                        self.total_errors += 1
                        self._log('error', f'Error procesando producto {producto.get("id")}: {str(e)}')
                
                offset += self.batch_size
                
                if len(productos) < self.batch_size:
                    break
                    
            except Exception as e:
                self._log('error', f'Error obteniendo productos (offset {offset}): {str(e)}')
                break

    def _process_producto(self, dux_producto, mapper):
        """Procesa un producto individual"""
        product_data = mapper.map_producto_to_product(dux_producto)
        
        if self.import_mode == 'test':
            self._log('info', f'[TEST] Producto: {product_data.get("name")} - {product_data.get("default_code")}')
            return
        
        # Buscar producto existente por código
        existing = None
        if dux_producto.get('codigo'):
            existing = self.env['product.product'].search([
                ('default_code', '=', dux_producto['codigo'])
            ], limit=1)
        
        if existing and self.update_existing:
            existing.write(product_data)
            self.total_updated += 1
            self._log('info', f'Producto actualizado: {product_data["name"]}')
        elif not existing:
            product = self.env['product.product'].create(product_data)
            self.total_created += 1
            self._log('info', f'Producto creado: {product.name}')

    def _import_ventas(self):
        """Importa ventas desde Dux"""
        self._log('info', 'Iniciando importación de ventas...')
        
        offset = 0
        mapper = self.env['dux.data.mapper']
        
        while True:
            try:
                response = self.connector_id.get_ventas(
                    fecha_desde=self.fecha_desde,
                    fecha_hasta=self.fecha_hasta,
                    limit=self.batch_size,
                    offset=offset
                )
                
                ventas = response.get('data', [])
                if not ventas:
                    break
                
                for venta in ventas:
                    try:
                        self._process_venta(venta, mapper)
                        self.total_processed += 1
                        
                    except Exception as e:
                        self.total_errors += 1
                        self._log('error', f'Error procesando venta {venta.get("numero")}: {str(e)}')
                
                offset += self.batch_size
                
                if len(ventas) < self.batch_size:
                    break
                    
            except Exception as e:
                self._log('error', f'Error obteniendo ventas (offset {offset}): {str(e)}')
                break

    def _process_venta(self, dux_venta, mapper):
        """Procesa una venta individual"""
        if self.import_mode == 'test':
            self._log('info', f'[TEST] Venta: {dux_venta.get("numero")} - {dux_venta.get("fecha")}')
            return
        
        sale_data = mapper.map_venta_to_sale_order(dux_venta)
        sale_order = self.env['sale.order'].create(sale_data)
        self.total_created += 1
        self._log('info', f'Venta creada: {sale_order.name}')

    def _import_compras(self):
        """Importa compras desde Dux"""
        self._log('info', 'Iniciando importación de compras...')
        
        offset = 0
        mapper = self.env['dux.data.mapper']
        
        while True:
            try:
                response = self.connector_id.get_compras(
                    fecha_desde=self.fecha_desde,
                    fecha_hasta=self.fecha_hasta,
                    limit=self.batch_size,
                    offset=offset
                )
                
                compras = response.get('data', [])
                if not compras:
                    break
                
                for compra in compras:
                    try:
                        self._process_compra(compra, mapper)
                        self.total_processed += 1
                        
                    except Exception as e:
                        self.total_errors += 1
                        self._log('error', f'Error procesando compra {compra.get("numero")}: {str(e)}')
                
                offset += self.batch_size
                
                if len(compras) < self.batch_size:
                    break
                    
            except Exception as e:
                self._log('error', f'Error obteniendo compras (offset {offset}): {str(e)}')
                break

    def _process_compra(self, dux_compra, mapper):
        """Procesa una compra individual"""
        if self.import_mode == 'test':
            self._log('info', f'[TEST] Compra: {dux_compra.get("numero")} - {dux_compra.get("fecha")}')
            return
        
        # Buscar proveedor
        proveedor = mapper._find_partner_by_dux_id(dux_compra.get('proveedor_id'))
        if not proveedor:
            self._log('warning', f'Proveedor no encontrado para compra {dux_compra.get("numero")}')
            return
        
        purchase_data = {
            'partner_id': proveedor.id,
            'date_order': mapper._parse_date(dux_compra.get('fecha')),
            'partner_ref': dux_compra.get('numero'),
            'notes': f"Importado desde Dux - ID: {dux_compra.get('id')}",
        }
        
        # Crear orden de compra
        purchase_order = self.env['purchase.order'].create(purchase_data)
        self.total_created += 1
        self._log('info', f'Compra creada: {purchase_order.name}')

    def _update_stock(self):
        """Actualiza stock desde Dux"""
        self._log('info', 'Iniciando actualización de stock...')
        
        if self.import_mode == 'test':
            self._log('info', '[TEST] Actualización de stock simulada')
            return
        
        try:
            response = self.connector_id.get_stock()
            stock_data = response.get('data', [])
            
            for item in stock_data:
                try:
                    product = self.env['product.product'].search([
                        ('default_code', '=', item.get('codigo_producto'))
                    ], limit=1)
                    
                    if product:
                        # Actualizar stock usando inventario
                        inventory = self.env['stock.quant'].search([
                            ('product_id', '=', product.id),
                            ('location_id.usage', '=', 'internal')
                        ], limit=1)
                        
                        new_qty = float(item.get('cantidad', 0))
                        if inventory:
                            inventory.quantity = new_qty
                        else:
                            # Crear nuevo registro de stock
                            self.env['stock.quant'].create({
                                'product_id': product.id,
                                'location_id': self.env.ref('stock.stock_location_stock').id,
                                'quantity': new_qty,
                            })
                        
                        self.total_updated += 1
                        self._log('info', f'Stock actualizado para {product.name}: {new_qty}')
                    else:
                        self._log('warning', f'Producto no encontrado: {item.get("codigo_producto")}')
                        
                except Exception as e:
                    self.total_errors += 1
                    self._log('error', f'Error actualizando stock {item.get("codigo_producto")}: {str(e)}')
                    
        except Exception as e:
            self._log('error', f'Error obteniendo datos de stock: {str(e)}')

    def _log(self, level, message):
        """Registra un log de la importación"""
        self.env['dux.import.log'].create({
            'wizard_id': self.id,
            'level': level,
            'message': message,
            'timestamp': fields.Datetime.now(),
        })
        
        # También logear en el sistema
        if level == 'error':
            _logger.error(f"Dux Import: {message}")
        elif level == 'warning':
            _logger.warning(f"Dux Import: {message}")
        else:
            _logger.info(f"Dux Import: {message}")

    def _clear_logs(self):
        """Limpia logs anteriores"""
        self.log_ids.unlink()
        self.total_processed = 0
        self.total_created = 0
        self.total_updated = 0
        self.total_errors = 0

    def _show_results(self):
        """Muestra los resultados de la importación"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Resultados de Importación',
            'res_model': 'dux.import.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'show_results': True}
        }

    def action_view_logs(self):
        """Abre la vista de logs"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Logs de Importación',
            'res_model': 'dux.import.log',
            'view_mode': 'tree,form',
            'domain': [('wizard_id', '=', self.id)],
            'context': {'default_wizard_id': self.id}
        }

class DuxImportLog(models.TransientModel):
    _name = 'dux.import.log'
    _description = 'Log de Importación Dux'
    _order = 'timestamp desc'

    wizard_id = fields.Many2one('dux.import.wizard', 'Wizard', ondelete='cascade')
    timestamp = fields.Datetime('Fecha/Hora', default=fields.Datetime.now)
    level = fields.Selection([
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error')
    ], string='Nivel', required=True)
    message = fields.Text('Mensaje', required=True)
    
    def name_get(self):
        """Nombre personalizado para logs"""
        result = []
        for record in self:
            name = f"[{record.level.upper()}] {record.timestamp.strftime('%H:%M:%S')} - {record.message[:50]}..."
            result.append((record.id, name))
        return result