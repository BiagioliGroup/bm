# models/supplier_integration.py
import requests
import json
import logging
import time
from datetime import datetime, timedelta
from odoo import models, fields, api, exceptions

_logger = logging.getLogger(__name__)

class SupplierIntegration(models.Model):
    _name = 'supplier.integration'
    _description = 'Integración con Proveedores'
    _rec_name = 'partner_id'
    
    partner_id = fields.Many2one('res.partner', 'Proveedor', required=True, 
                                domain=[('is_company', '=', True), ('supplier_rank', '>', 0)])
    name = fields.Char('Nombre Integración', compute='_compute_name', store=True)
    integration_type = fields.Selection([
        ('wps', 'WPS-inc API'),
        ('csv', 'Importación CSV'),
        ('xml', 'Feed XML'),
        ('json', 'API JSON Genérica'),
        ('custom', 'Integración Personalizada')
    ], required=True, default='wps')
    
    # Configuración API
    api_base_url = fields.Char('URL Base API', required=True)
    api_token = fields.Char('Token API', required=True)
    api_version = fields.Char('Versión API', default='v4')
    
    # Configuración de importación
    is_active = fields.Boolean('Activo', default=True)
    auto_import = fields.Boolean('Importación Automática', default=False)
    import_interval_hours = fields.Integer('Intervalo Importación (horas)', default=24)
    last_import = fields.Datetime('Última Importación')
    
    # Filtros de importación
    min_stock_qty = fields.Integer('Stock Mínimo', default=1, help="Solo importar productos con stock >= esta cantidad")
    max_price = fields.Float('Precio Máximo', help="Solo importar productos con precio <= este valor")
    category_filter = fields.Text('Filtro Categorías', help="Lista de categorías separadas por coma")
    
    # Configuración de costos
    markup_percentage = fields.Float('Markup %', default=20.0)
    import_cost_percentage = fields.Float('Costo Importación %', default=15.0)
    
    # Estadísticas
    total_products_available = fields.Integer('Productos Disponibles', readonly=True)
    products_imported = fields.Integer('Productos Importados', readonly=True)
    last_sync_status = fields.Selection([
        ('success', 'Exitoso'),
        ('error', 'Error'),
        ('pending', 'Pendiente')
    ], readonly=True)
    
    @api.depends('partner_id', 'integration_type')
    def _compute_name(self):
        for record in self:
            if record.partner_id and record.integration_type:
                record.name = f"{record.partner_id.name} - {dict(record._fields['integration_type'].selection)[record.integration_type]}"
            elif record.partner_id:
                record.name = f"{record.partner_id.name} - Nueva Integración"
            else:
                record.name = "Nueva Integración"
    
    @api.model
    def create(self, vals):
        """Al crear integración, agregar información al proveedor"""
        integration = super().create(vals)
        if integration.partner_id:
            integration.partner_id.message_post(
                body=f"Integración API configurada: {integration.integration_type}",
                message_type='notification'
            )
        return integration
    
    def test_connection(self):
        """Prueba la conexión con la API del proveedor"""
        try:
            if self.integration_type == 'wps':
                return self._test_wps_connection()
            else:
                raise exceptions.UserError(f"Tipo de integración '{self.integration_type}' no implementado aún")
        except Exception as e:
            raise exceptions.UserError(f"Error de conexión: {str(e)}")
    
    def _test_wps_connection(self):
        """Prueba específica para WPS API - CORREGIDA"""
        headers = {
            'Authorization': f'Token {self.api_token}',
            'Content-Type': 'application/json'
        }
        
        # Usar endpoint que existe: /products con límite muy bajo para test
        test_url = f"{self.api_base_url}/products"
        params = {
            'page[size]': 1  # Solo 1 producto para probar la conexión
        }
        
        try:
            response = requests.get(test_url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # WPS devuelve estructura: {"data": [...], "meta": {...}}
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Conexión Exitosa',
                        'message': f"Conectado a WPS API. Productos disponibles para importar.",
                        'type': 'success',
                    }
                }
            elif response.status_code == 401:
                raise exceptions.UserError("Token de API inválido. Verifica tus credenciales.")
            elif response.status_code == 403:
                raise exceptions.UserError("No tienes permisos para acceder a la API. Contacta a WPS.")
            else:
                raise exceptions.UserError(f"Error HTTP: {response.status_code}")
                
        except requests.exceptions.Timeout:
            raise exceptions.UserError("Tiempo de espera agotado. Verifica tu conexión a internet.")
        except requests.exceptions.ConnectionError:
            raise exceptions.UserError("No se pudo conectar a WPS. Verifica la URL base.")
        except Exception as e:
            raise exceptions.UserError(f"Error de conexión: {str(e)}")
    
    def sync_products(self):
        """Sincroniza productos desde el proveedor"""
        if not self.is_active:
            raise exceptions.UserError("La integración está desactivada")
        
        try:
            if self.integration_type == 'wps':
                return self._sync_wps_products()
            else:
                raise exceptions.UserError(f"Sincronización para '{self.integration_type}' no implementada aún")
        except Exception as e:
            _logger.error(f"Error sincronizando productos: {e}")
            self.last_sync_status = 'error'
            raise
    
    def _sync_wps_products(self):
        """Sincronización específica para WPS - CORREGIDA"""
        headers = {
            'Authorization': f'Token {self.api_token}',
            'Content-Type': 'application/json'
        }
        
        # URL corregida para productos
        products_url = f"{self.api_base_url}/products"
        params = {
            'page[size]': 50,  # WPS recomienda máximo 50-100 por página
            'include': 'inventory,dealer_pricing'  # Incluir inventario y precios
        }
        
        all_products = []
        cursor = None
        
        # Usar paginación cursor-based de WPS
        while True:
            if cursor:
                params['page[cursor]'] = cursor
            
            response = requests.get(products_url, headers=headers, params=params, timeout=30)
            
            if response.status_code != 200:
                raise exceptions.UserError(f"Error API WPS: {response.status_code} - {response.text}")
            
            data = response.json()
            products = data.get('data', [])
            
            if not products:
                break
            
            # Filtrar productos con stock mínimo
            filtered_products = self._filter_wps_products_by_stock(products)
            all_products.extend(filtered_products)
            
            # Verificar si hay más páginas usando cursor
            meta = data.get('meta', {})
            cursor_info = meta.get('cursor', {})
            cursor = cursor_info.get('next')
            
            if not cursor:  # No más páginas
                break
                
            time.sleep(0.5)  # Rate limiting
            
            # Límite de seguridad para evitar importaciones masivas
            if len(all_products) >= 500:
                break
        
        # Procesar productos obtenidos
        self.total_products_available = len(all_products)
        processed = self._process_wps_products(all_products)
        
        self.products_imported = processed
        self.last_import = fields.Datetime.now()
        self.last_sync_status = 'success'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Sincronización Completada',
                'message': f"Procesados {processed} productos de {len(all_products)} disponibles",
                'type': 'success',
            }
        }
    
    def _process_products(self, products_data):
        """Procesa los productos obtenidos y los crea/actualiza en Odoo"""
        processed_count = 0
        
        for product_data in products_data:
            try:
                # Buscar si el producto ya existe por SKU del proveedor
                existing_product = self.env['product.template'].search([
                    ('default_code', '=', product_data.get('sku')),
                    ('supplier_integration_id', '=', self.id)
                ], limit=1)
                
                product_vals = self._prepare_product_values(product_data)
                
                if existing_product:
                    existing_product.write(product_vals)
                else:
                    self.env['product.template'].create(product_vals)
                
                processed_count += 1
                
                # Log de importación
                self._create_import_log('success', product_data.get('sku'), 
                                      f"Producto procesado: {product_data.get('name', 'Sin nombre')}")
                
            except Exception as e:
                _logger.error(f"Error procesando producto {product_data.get('sku')}: {e}")
                self._create_import_log('error', product_data.get('sku'), str(e))
                
        return processed_count
    
    def _filter_wps_products_by_stock(self, products):
        """Filtra productos WPS por stock usando datos incluidos"""
        filtered = []
        for product in products:
            # Obtener datos de inventario incluidos
            included_data = product.get('included', [])
            total_stock = 0
            
            # Buscar inventory data en included
            for include_item in included_data:
                if include_item.get('type') == 'inventory':
                    stock_qty = include_item.get('attributes', {}).get('quantity', 0)
                    if stock_qty == 25:  # WPS ceiling
                        stock_qty = 25  # Mantener como 25+ disponible
                    total_stock += stock_qty
            
            # Si no hay datos de inventory en included, asumir que tiene stock
            if not any(item.get('type') == 'inventory' for item in included_data):
                total_stock = self.min_stock_qty  # Asumir stock mínimo
            
            if total_stock >= self.min_stock_qty:
                product['_calculated_stock'] = total_stock
                filtered.append(product)
        
        return filtered
    
    def _process_wps_products(self, products_data):
        """Procesa productos WPS con estructura de API v4"""
        processed_count = 0
        
        for product_data in products_data:
            try:
                # WPS structure: product_data['attributes'] contiene los datos
                attributes = product_data.get('attributes', {})
                
                # Obtener items relacionados (SKUs)
                relationships = product_data.get('relationships', {})
                items_rel = relationships.get('items', {}).get('data', [])
                
                if not items_rel:
                    # Si no hay items, usar el producto principal
                    self._process_single_wps_product(product_data, attributes, product_data.get('id'))
                    processed_count += 1
                else:
                    # Procesar cada item (SKU) del producto
                    for item_ref in items_rel:
                        item_id = item_ref.get('id')
                        if item_id:
                            # Buscar los datos del item en included
                            item_data = self._find_included_item(product_data, item_id)
                            if item_data:
                                self._process_single_wps_product(product_data, attributes, item_data)
                                processed_count += 1
                
            except Exception as e:
                _logger.error(f"Error procesando producto WPS: {e}")
                self._create_import_log('error', 'N/A', str(e))
                
        return processed_count
    
    def _find_included_item(self, product_data, item_id):
        """Busca los datos de un item específico en la sección included"""
        included_data = product_data.get('included', [])
        for item in included_data:
            if item.get('type') == 'items' and item.get('id') == item_id:
                return item
        return None
    
    def _process_single_wps_product(self, product_data, product_attrs, item_data):
        """Procesa un producto/item individual de WPS"""
        if isinstance(item_data, str):
            # Si item_data es solo un ID, usar datos del producto principal
            sku = product_attrs.get('sku', item_data)
            item_attrs = {}
        else:
            # Si item_data es un objeto completo
            item_attrs = item_data.get('attributes', {})
            sku = item_attrs.get('sku') or product_attrs.get('sku')
        
        if not sku:
            return
        
        # Buscar producto existente
        existing_product = self.env['product.template'].search([
            ('default_code', '=', sku),
            ('supplier_integration_id', '=', self.id)
        ], limit=1)
        
        # Preparar valores del producto
        product_vals = self._prepare_wps_product_values(product_attrs, item_attrs, product_data)
        
        try:
            if existing_product:
                existing_product.write(product_vals)
            else:
                self.env['product.template'].create(product_vals)
            
            # Log de importación
            self._create_import_log('success', sku, 
                                  f"Producto WPS procesado: {product_vals.get('name', 'Sin nombre')}")
        except Exception as e:
            self._create_import_log('error', sku, f"Error creando producto: {str(e)}")
    
    def _prepare_wps_product_values(self, product_attrs, item_attrs, full_product_data):
        """Prepara valores específicos para productos WPS"""
        
        # Obtener precio desde dealer_pricing incluido
        base_price = 0
        included_data = full_product_data.get('included', [])
        
        for include_item in included_data:
            if include_item.get('type') == 'dealer_pricing':
                pricing_attrs = include_item.get('attributes', {})
                base_price = float(pricing_attrs.get('price', 0))
                break
        
        # Si no hay pricing incluido, usar precio por defecto
        if base_price == 0:
            base_price = float(product_attrs.get('price', 0))
        
        # Calcular costos
        import_cost = base_price * (self.import_cost_percentage / 100)
        total_cost = base_price + import_cost
        sale_price = total_cost * (1 + self.markup_percentage / 100)
        
        # Construir nombre del producto
        product_name = product_attrs.get('name', 'Producto WPS')
        brand_name = product_attrs.get('brand', '')
        if brand_name and brand_name not in product_name:
            product_name = f"{brand_name} {product_name}"
        
        # SKU del item o del producto
        sku = item_attrs.get('sku') or product_attrs.get('sku')
        
        vals = {
            'name': product_name,
            'default_code': sku,
            'list_price': sale_price,
            'standard_price': total_cost,
            'type': 'product',
            'purchase_ok': True,
            'sale_ok': True,
            'supplier_integration_id': self.id,
            'description': product_attrs.get('description', ''),
            'original_price': base_price,
            'import_cost': import_cost,
            'last_sync_date': fields.Datetime.now(),
        }
        
        # Agregar información del proveedor
        vals['seller_ids'] = [(0, 0, {
            'partner_id': self.partner_id.id,
            'price': base_price,
            'min_qty': 1,
            'product_code': sku,
        })]
        
        # Stock calculado si está disponible
        if '_calculated_stock' in full_product_data:
            vals['qty_available'] = full_product_data['_calculated_stock']
        
        return vals
    
    def _prepare_product_values(self, product_data):
        """Prepara los valores del producto para Odoo"""
        # Precio base del proveedor
        base_price = float(product_data.get('price', 0))
        
        # Calcular costo de importación
        import_cost = base_price * (self.import_cost_percentage / 100)
        total_cost = base_price + import_cost
        
        # Calcular precio de venta con markup
        sale_price = total_cost * (1 + self.markup_percentage / 100)
        
        vals = {
            'name': product_data.get('name', 'Producto Importado'),
            'default_code': product_data.get('sku'),
            'list_price': sale_price,
            'standard_price': total_cost,
            'type': 'product',
            'purchase_ok': True,
            'sale_ok': True,
            'supplier_integration_id': self.id,
            'description': product_data.get('description', ''),
        }
        
        # Agregar información del proveedor
        vals['seller_ids'] = [(0, 0, {
            'partner_id': self.partner_id.id,
            'price': base_price,
            'min_qty': 1,
            'product_code': product_data.get('sku'),
        })]
        
        # Actualizar stock si está disponible
        if product_data.get('stock_quantity'):
            vals['qty_available'] = int(product_data.get('stock_quantity', 0))
        
        return vals
    
    def _create_import_log(self, status, product_sku, message):
        """Crea log de importación"""
        self.env['product.import.log'].create({
            'supplier_integration_id': self.id,
            'product_sku': product_sku,
            'status': status,
            'message': message,
            'import_date': fields.Datetime.now()
        })

# models/product_template.py
class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    supplier_integration_id = fields.Many2one('supplier.integration', 'Integración Proveedor')
    original_price = fields.Float('Precio Original Proveedor')
    import_cost = fields.Float('Costo Importación')
    last_sync_date = fields.Datetime('Última Sincronización')

# models/import_log.py
class ProductImportLog(models.Model):
    _name = 'product.import.log'
    _description = 'Log de Importación de Productos'
    _order = 'import_date desc'
    
    supplier_integration_id = fields.Many2one('supplier.integration', 'Proveedor', required=True)
    product_sku = fields.Char('SKU Producto')
    status = fields.Selection([
        ('success', 'Éxito'),
        ('error', 'Error'),
        ('warning', 'Advertencia')
    ], required=True)
    message = fields.Text('Mensaje')
    import_date = fields.Datetime('Fecha Importación', default=fields.Datetime.now)