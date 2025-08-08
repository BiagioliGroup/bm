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
    name = fields.Char('Nombre', related='partner_id.name', readonly=True)
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
        """Prueba específica para WPS API"""
        headers = {
            'Authorization': f'Token {self.api_token}',
            'Content-Type': 'application/json'
        }
        
        # Test endpoint básico
        response = requests.get(
            f"{self.api_base_url}/api/{self.api_version}/user/",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            user_data = response.json()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Conexión Exitosa',
                    'message': f"Conectado como: {user_data.get('username', 'Usuario')}",
                    'type': 'success',
                }
            }
        else:
            raise exceptions.UserError(f"Error HTTP: {response.status_code}")
    
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
        """Sincronización específica para WPS"""
        headers = {
            'Authorization': f'Token {self.api_token}',
            'Content-Type': 'application/json'
        }
        
        # Obtener productos con stock
        products_url = f"{self.api_base_url}/api/{self.api_version}/products/"
        params = {
            'page_size': 100,
            'stock_gt': self.min_stock_qty - 1  # Mayor que min_stock_qty - 1
        }
        
        if self.max_price:
            params['price_lte'] = self.max_price
        
        all_products = []
        page = 1
        
        while True:
            params['page'] = page
            response = requests.get(products_url, headers=headers, params=params, timeout=30)
            
            if response.status_code != 200:
                raise exceptions.UserError(f"Error API WPS: {response.status_code}")
            
            data = response.json()
            products = data.get('results', [])
            
            if not products:
                break
                
            all_products.extend(products)
            
            # Verificar si hay más páginas
            if not data.get('next'):
                break
                
            page += 1
            time.sleep(0.5)  # Rate limiting
        
        # Procesar productos obtenidos
        self.total_products_available = len(all_products)
        processed = self._process_products(all_products)
        
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