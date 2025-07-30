# -*- coding: utf-8 -*-
import json
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class DuxImportWizard(models.TransientModel):
    _name = 'dux.import.wizard'
    _description = 'Asistente de Importación Dux'

    # Configuración general
    connector_id = fields.Many2one('dux.connector', 'Conexión Dux', required=True)
    import_mode = fields.Selection([
        ('fetch_only', 'Solo Obtener Datos (Crear Lotes)'),
        ('process_batches', 'Procesar Lotes Existentes'),
        ('fetch_and_process', 'Obtener y Procesar Inmediatamente')
    ], string='Modo', default='fetch_only', required=True)
    
    # Selección de datos a importar
    import_clientes = fields.Boolean('Importar Clientes', default=False)
    import_productos = fields.Boolean('Importar Productos', default=False)
    import_ventas = fields.Boolean('Importar Ventas', default=True)
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
    
    # Lotes existentes para procesar
    available_batch_ids = fields.Many2many('dux.import.batch', string='Lotes Disponibles',
                                          domain=[('state', '=', 'raw')])
    
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
    
    # Lotes creados en esta sesión
    created_batch_ids = fields.Many2many('dux.import.batch', 'wizard_batch_created_rel',
                                        string='Lotes Creados', readonly=True)
    
    @api.onchange('import_mode')
    def _onchange_import_mode(self):
        """Actualizar dominio de lotes disponibles según modo"""
        if self.import_mode == 'process_batches':
            return {
                'domain': {
                    'available_batch_ids': [('state', '=', 'raw')]
                }
            }
    
    def action_import(self):
        """Ejecuta importación según modo seleccionado"""
        self.ensure_one()
        
        try:
            self.state = 'running'
            self._clear_logs()
            
            # Verificar conexión
            if not self.connector_id:
                raise UserError('Debe seleccionar una conexión Dux válida')
            
            self.connector_id.test_connection()
            
            if self.import_mode == 'fetch_only':
                return self._fetch_data_to_batches()
            elif self.import_mode == 'process_batches':
                return self._process_existing_batches()
            elif self.import_mode == 'fetch_and_process':
                self._fetch_data_to_batches()
                return self._process_created_batches()
            else:
                raise UserError('Modo de importación no válido')
            
        except Exception as e:
            self.state = 'error'
            self._log('error', f'Error en importación: {str(e)}')
            # En lugar de raise, devolver el wizard actualizado
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'dux.import.wizard',
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
                'context': {'show_error': True}
            }
    
    def _fetch_data_to_batches(self):
        """Obtiene datos de Dux y los guarda en lotes JSON"""
        self._log('info', 'Iniciando obtención de datos desde Dux...')
        
        created_batches = self.env['dux.import.batch']
        
        try:
            # Obtener ventas
            if self.import_ventas:
                try:
                    batch = self._fetch_ventas_to_batch()
                    if batch:
                        created_batches |= batch
                except Exception as e:
                    self._log('error', f'Error obteniendo ventas: {str(e)}')
            
            # Obtener compras
            if self.import_compras:
                try:
                    batch = self._fetch_compras_to_batch()
                    if batch:
                        created_batches |= batch
                except Exception as e:
                    self._log('error', f'Error obteniendo compras: {str(e)}')
            
            # Obtener pagos
            if self.import_pagos:
                try:
                    batch = self._fetch_pagos_to_batch()
                    if batch:
                        created_batches |= batch
                except Exception as e:
                    self._log('error', f'Error obteniendo pagos: {str(e)}')
            
            # Obtener cobros
            if self.import_cobros:
                try:
                    batch = self._fetch_cobros_to_batch()
                    if batch:
                        created_batches |= batch
                except Exception as e:
                    self._log('error', f'Error obteniendo cobros: {str(e)}')
            
            # Obtener clientes (sin filtro de fechas)
            if self.import_clientes:
                try:
                    batch = self._fetch_clientes_to_batch()
                    if batch:
                        created_batches |= batch
                except Exception as e:
                    self._log('error', f'Error obteniendo clientes: {str(e)}')
            
            # Obtener productos (sin filtro de fechas)
            if self.import_productos:
                try:
                    batch = self._fetch_productos_to_batch()
                    if batch:
                        created_batches |= batch
                except Exception as e:
                    self._log('error', f'Error obteniendo productos: {str(e)}')
            
            self.created_batch_ids = [(6, 0, created_batches.ids)]
            self.state = 'done'
            
            if created_batches:
                self._log('info', f'Datos obtenidos exitosamente. {len(created_batches)} lotes creados.')
            else:
                self._log('warning', 'No se crearon lotes. Verificar configuración y conectividad.')
            
            return self._show_batch_results(created_batches)
            
        except Exception as e:
            self.state = 'error'
            self._log('error', f'Error obteniendo datos: {str(e)}')
            raise
    
    def _fetch_ventas_to_batch(self):
        """Obtiene ventas y crea lote JSON"""
        self._log('info', 'Obteniendo ventas desde Dux...')
        
        all_ventas = []
        offset = 0
        
        # Log de parámetros de búsqueda
        self._log('info', f'Parámetros: fecha_desde={self.fecha_desde}, fecha_hasta={self.fecha_hasta}, batch_size={self.batch_size}')
        
        while True:
            try:
                self._log('info', f'Llamando API con offset={offset}')
                
                response = self.connector_id.get_ventas(
                    fecha_desde=self.fecha_desde,
                    fecha_hasta=self.fecha_hasta,
                    limit=self.batch_size,
                    offset=offset
                )
                
                # DEBUG: Logear la respuesta completa
                self._log('info', f'Respuesta API (tipo: {type(response)}): {str(response)[:500]}...')
                
                # Manejar diferentes estructuras de respuesta
                if isinstance(response, dict):
                    ventas = response.get('data', response.get('results', response.get('items', [])))
                    # Log adicional de la estructura
                    self._log('info', f'Keys en respuesta dict: {list(response.keys()) if response else "None"}')
                elif isinstance(response, list):
                    ventas = response
                else:
                    ventas = []
                    self._log('warning', f'Tipo de respuesta inesperado: {type(response)}')
                
                self._log('info', f'Ventas extraídas (tipo: {type(ventas)}): {len(ventas) if isinstance(ventas, list) else "No es lista"}')
                
                if not ventas:
                    self._log('info', 'Sin más ventas, finalizando bucle')
                    break
                
                # Si hay ventas, loguear la primera como muestra
                if ventas and isinstance(ventas, list) and len(ventas) > 0:
                    self._log('info', f'Muestra de primera venta: {str(ventas[0])[:200]}...')
                
                all_ventas.extend(ventas)
                offset += self.batch_size
                
                self._log('info', f'Acumuladas {len(all_ventas)} ventas total')
                
                # Evitar bucle infinito
                if len(ventas) < self.batch_size:
                    self._log('info', f'Menos ventas que batch_size ({len(ventas)} < {self.batch_size}), finalizando')
                    break
                    
            except Exception as e:
                self._log('error', f'Error en llamada API (offset {offset}): {str(e)}')
                break
        
        self._log('info', f'Total ventas obtenidas: {len(all_ventas)}')
        
        if all_ventas:
            # Crear lote
            batch_name = self.env['dux.import.batch'].generate_batch_name(
                'ventas', self.fecha_desde, self.fecha_hasta
            )
            
            batch = self.env['dux.import.batch'].create({
                'batch_name': batch_name,
                'connector_id': self.connector_id.id,
                'data_type': 'ventas',
                'fecha_desde': self.fecha_desde,
                'fecha_hasta': self.fecha_hasta,
                'batch_size': self.batch_size,
                'raw_data_json': json.dumps(all_ventas),
                'state': 'raw'
            })
            
            self._log('info', f'Lote de ventas creado: {batch.batch_name} ({len(all_ventas)} registros)')
            return batch
        else:
            self._log('warning', 'No se encontraron ventas en el rango especificado')
            return None
    
    def _fetch_compras_to_batch(self):
        """Obtiene compras y crea lote JSON"""
        self._log('info', 'Obteniendo compras desde Dux...')
        
        all_compras = []
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
                
                all_compras.extend(compras)
                offset += self.batch_size
                
                if len(compras) < self.batch_size:
                    break
                    
            except Exception as e:
                self._log('error', f'Error obteniendo compras (offset {offset}): {str(e)}')
                break
        
        if all_compras:
            batch_name = self.env['dux.import.batch'].generate_batch_name(
                'compras', self.fecha_desde, self.fecha_hasta
            )
            
            batch = self.env['dux.import.batch'].create({
                'batch_name': batch_name,
                'connector_id': self.connector_id.id,
                'data_type': 'compras',
                'fecha_desde': self.fecha_desde,
                'fecha_hasta': self.fecha_hasta,
                'batch_size': self.batch_size,
                'raw_data_json': json.dumps(all_compras),
                'state': 'raw'
            })
            
            self._log('info', f'Lote de compras creado: {batch.batch_name} ({len(all_compras)} registros)')
            return batch
        else:
            self._log('warning', 'No se encontraron compras en el rango especificado')
            return None
    
    def _fetch_pagos_to_batch(self):
        """Obtiene pagos y crea lote JSON"""
        self._log('info', 'Obteniendo pagos desde Dux...')
        
        all_pagos = []
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
                
                all_pagos.extend(pagos)
                offset += self.batch_size
                
                if len(pagos) < self.batch_size:
                    break
                    
            except Exception as e:
                self._log('error', f'Error obteniendo pagos (offset {offset}): {str(e)}')
                break
        
        if all_pagos:
            batch_name = self.env['dux.import.batch'].generate_batch_name(
                'pagos', self.fecha_desde, self.fecha_hasta
            )
            
            batch = self.env['dux.import.batch'].create({
                'batch_name': batch_name,
                'connector_id': self.connector_id.id,
                'data_type': 'pagos',
                'fecha_desde': self.fecha_desde,
                'fecha_hasta': self.fecha_hasta,
                'batch_size': self.batch_size,
                'raw_data_json': json.dumps(all_pagos),
                'state': 'raw'
            })
            
            self._log('info', f'Lote de pagos creado: {batch.batch_name} ({len(all_pagos)} registros)')
            return batch
        else:
            self._log('warning', 'No se encontraron pagos en el rango especificado')
            return None
    
    def _fetch_cobros_to_batch(self):
        """Obtiene cobros y crea lote JSON"""
        self._log('info', 'Obteniendo cobros desde Dux...')
        
        all_cobros = []
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
                
                all_cobros.extend(cobros)
                offset += self.batch_size
                
                if len(cobros) < self.batch_size:
                    break
                    
            except Exception as e:
                self._log('error', f'Error obteniendo cobros (offset {offset}): {str(e)}')
                break
        
        if all_cobros:
            batch_name = self.env['dux.import.batch'].generate_batch_name(
                'cobros', self.fecha_desde, self.fecha_hasta
            )
            
            batch = self.env['dux.import.batch'].create({
                'batch_name': batch_name,
                'connector_id': self.connector_id.id,
                'data_type': 'cobros',
                'fecha_desde': self.fecha_desde,
                'fecha_hasta': self.fecha_hasta,
                'batch_size': self.batch_size,
                'raw_data_json': json.dumps(all_cobros),
                'state': 'raw'
            })
            
            self._log('info', f'Lote de cobros creado: {batch.batch_name} ({len(all_cobros)} registros)')
            return batch
        else:
            self._log('warning', 'No se encontraron cobros en el rango especificado')
            return None
    
    def _fetch_clientes_to_batch(self):
        """Obtiene clientes y crea lote JSON"""
        self._log('info', 'Obteniendo clientes desde Dux...')
        
        all_clientes = []
        offset = 0
        
        while True:
            try:
                response = self.connector_id.get_clientes(
                    limit=self.batch_size,
                    offset=offset
                )
                
                clientes = response.get('data', []) if isinstance(response, dict) else response
                if not clientes:
                    break
                
                all_clientes.extend(clientes)
                offset += self.batch_size
                
                if len(clientes) < self.batch_size:
                    break
                    
            except Exception as e:
                self._log('error', f'Error obteniendo clientes (offset {offset}): {str(e)}')
                break
        
        if all_clientes:
            batch_name = self.env['dux.import.batch'].generate_batch_name('clientes')
            
            batch = self.env['dux.import.batch'].create({
                'batch_name': batch_name,
                'connector_id': self.connector_id.id,
                'data_type': 'clientes',
                'batch_size': self.batch_size,
                'raw_data_json': json.dumps(all_clientes),
                'state': 'raw'
            })
            
            self._log('info', f'Lote de clientes creado: {batch.batch_name} ({len(all_clientes)} registros)')
            return batch
        else:
            self._log('warning', 'No se encontraron clientes')
            return None
    
    def _fetch_productos_to_batch(self):
        """Obtiene productos y crea lote JSON"""
        self._log('info', 'Obteniendo productos desde Dux...')
        
        all_productos = []
        offset = 0
        
        while True:
            try:
                response = self.connector_id.get_productos(
                    limit=self.batch_size,
                    offset=offset
                )
                
                productos = response.get('data', []) if isinstance(response, dict) else response
                if not productos:
                    break
                
                all_productos.extend(productos)
                offset += self.batch_size
                
                if len(productos) < self.batch_size:
                    break
                    
            except Exception as e:
                self._log('error', f'Error obteniendo productos (offset {offset}): {str(e)}')
                break
        
        if all_productos:
            batch_name = self.env['dux.import.batch'].generate_batch_name('productos')
            
            batch = self.env['dux.import.batch'].create({
                'batch_name': batch_name,
                'connector_id': self.connector_id.id,
                'data_type': 'productos',
                'batch_size': self.batch_size,
                'raw_data_json': json.dumps(all_productos),
                'state': 'raw'
            })
            
            self._log('info', f'Lote de productos creado: {batch.batch_name} ({len(all_productos)} registros)')
            return batch
        else:
            self._log('warning', 'No se encontraron productos')
            return None
    
    def _process_existing_batches(self):
        """Procesa lotes existentes seleccionados"""
        if not self.available_batch_ids:
            raise UserError('Debe seleccionar al menos un lote para procesar')
        
        self._log('info', f'Procesando {len(self.available_batch_ids)} lotes seleccionados...')
        
        for batch in self.available_batch_ids:
            try:
                batch.action_process_batch()
                self.total_processed += batch.processed_count
                self.total_errors += batch.error_count
                self._log('info', f'Lote procesado: {batch.batch_name}')
            except Exception as e:
                self.total_errors += 1
                self._log('error', f'Error procesando lote {batch.batch_name}: {str(e)}')
        
        self.state = 'done'
        return self._show_processing_results()
    
    def _process_created_batches(self):
        """Procesa lotes creados en esta sesión"""
        if not self.created_batch_ids:
            self._log('warning', 'No hay lotes creados para procesar')
            return self._show_processing_results()
        
        self._log('info', f'Procesando {len(self.created_batch_ids)} lotes creados...')
        
        for batch in self.created_batch_ids:
            try:
                batch.action_process_batch()
                self.total_processed += batch.processed_count
                self.total_errors += batch.error_count
                self._log('info', f'Lote procesado: {batch.batch_name}')
            except Exception as e:
                self.total_errors += 1
                self._log('error', f'Error procesando lote {batch.batch_name}: {str(e)}')
        
        self.state = 'done'
        return self._show_processing_results()
    
    def _show_batch_results(self, batches):
        """Muestra resultados de lotes creados"""
        if not batches:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Importación Completada',
                'res_model': 'dux.import.wizard',
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
                'context': {'show_results': True}
            }
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Lotes Creados',
            'res_model': 'dux.import.batch',
            'view_mode': 'list,form',
            'domain': [('id', 'in', batches.ids)],
            'context': {'default_connector_id': self.connector_id.id}
        }
    
    def _show_processing_results(self):
        """Muestra resultados del procesamiento"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Resultados de Importación',
            'res_model': 'dux.import.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'show_results': True}
        }
    
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