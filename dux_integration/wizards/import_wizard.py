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

    def action_import(self):
        """Ejecuta la importación"""
        self.ensure_one()
        
        try:
            self.state = 'running'
            self._clear_logs()
            
            # Verificar conexión
            self.connector_id.test_connection()
            
            # Ejecutar importaciones seleccionadas
            if self.import_clientes:
                self._import_clientes()
            
            if self.import_productos:
                self._import_productos()
                
            if self.import_ventas:
                self._import_ventas()
                
            if self.import_compras:
                self._import_compras()
                
            if self.import_stock:
                self._update_stock()
            
            self.state = 'done'
            self._log('info', 'Importación completada exitosamente')
            
            return self._show_results()
            
        except Exception as e:
            self.state = 'error'
            self._log('error', f'Error general: {str(e)}')
            _logger.error(f"Error en importación Dux: {str(e)}")
            raise UserError(f"Error en importación: {str(e)}")

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