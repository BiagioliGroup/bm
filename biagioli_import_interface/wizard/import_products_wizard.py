# wizard/import_products_wizard.py
import json
from odoo import models, fields, api, exceptions

class ImportProductsWizard(models.TransientModel):
    _name = 'import.products.wizard'
    _description = 'Asistente de Importación de Productos'
    
    supplier_integration_id = fields.Many2one('supplier.integration', 'Proveedor', required=True)
    import_mode = fields.Selection([
        ('all', 'Todos los productos con stock'),
        ('filtered', 'Solo productos filtrados'),
        ('specific', 'SKUs específicos')
    ], default='all', required=True)
    
    # Filtros específicos
    specific_skus = fields.Text('SKUs Específicos', help="Un SKU por línea")
    category_filter = fields.Char('Filtro Categorías', help="Separado por comas")
    min_stock = fields.Integer('Stock Mínimo', default=1)
    max_price = fields.Float('Precio Máximo')
    
    # Vista previa
    preview_products = fields.Text('Productos a Importar', readonly=True)
    preview_count = fields.Integer('Cantidad', readonly=True, default=0)
    
    @api.onchange('supplier_integration_id', 'import_mode', 'specific_skus', 'category_filter', 'min_stock', 'max_price')
    def _onchange_filters(self):
        """Auto-actualizar vista previa cuando cambian los filtros"""
        if self.supplier_integration_id:
            self.preview_import()
    
    def preview_import(self):
        """Obtiene vista previa de productos a importar"""
        if not self.supplier_integration_id:
            return
        
        try:
            # Obtener productos según filtros
            products = self._get_filtered_products()
            
            # Preparar vista previa
            preview_lines = []
            for product in products[:50]:  # Máximo 50 en vista previa
                preview_lines.append(f"• {product.get('sku')} - {product.get('name')} - ${product.get('price', 0)}")
            
            if len(products) > 50:
                preview_lines.append(f"... y {len(products) - 50} productos más")
            
            self.preview_products = '\n'.join(preview_lines)
            self.preview_count = len(products)
            
        except Exception as e:
            self.preview_products = f"Error obteniendo vista previa: {str(e)}"
            self.preview_count = 0
    
    def _get_filtered_products(self):
        """Obtiene productos filtrados desde la API"""
        integration = self.supplier_integration_id
        
        if integration.integration_type == 'wps':
            return self._get_wps_products()
        else:
            raise exceptions.UserError("Tipo de proveedor no soportado")
    
    def _get_wps_products(self):
        """Obtiene productos desde WPS API con filtros aplicados"""
        import requests
        import time
        
        integration = self.supplier_integration_id
        headers = {
            'Authorization': f'Token {integration.api_token}',
            'Content-Type': 'application/json'
        }
        
        # Preparar parámetros según modo
        params = {
            'page_size': 100,
            'stock_gt': (self.min_stock or integration.min_stock_qty) - 1
        }
        
        if self.max_price or integration.max_price:
            params['price_lte'] = self.max_price or integration.max_price
        
        # Obtener productos
        products_url = f"{integration.api_base_url}/api/{integration.api_version}/products/"
        all_products = []
        page = 1
        
        while page <= 5:  # Límite de seguridad para vista previa
            params['page'] = page
            response = requests.get(products_url, headers=headers, params=params, timeout=30)
            
            if response.status_code != 200:
                raise exceptions.UserError(f"Error API WPS: {response.status_code}")
            
            data = response.json()
            products = data.get('results', [])
            
            if not products:
                break
                
            all_products.extend(products)
            
            if not data.get('next'):
                break
                
            page += 1
            time.sleep(0.5)  # Rate limiting
        
        # Aplicar filtros adicionales
        filtered_products = self._apply_additional_filters(all_products)
        
        return filtered_products
    
    def _apply_additional_filters(self, products):
        """Aplica filtros adicionales a los productos obtenidos"""
        filtered = products
        
        # Filtro por SKUs específicos
        if self.import_mode == 'specific' and self.specific_skus:
            target_skus = set(sku.strip().upper() for sku in self.specific_skus.split('\n') if sku.strip())
            filtered = [p for p in filtered if p.get('sku', '').upper() in target_skus]
        
        # Filtro por categorías
        if self.category_filter:
            categories = [cat.strip().lower() for cat in self.category_filter.split(',') if cat.strip()]
            filtered = [p for p in filtered 
                       if any(cat in p.get('category', '').lower() for cat in categories)]
        
        return filtered
    
    def import_products(self):
        """Ejecuta la importación de productos"""
        if not self.supplier_integration_id:
            raise exceptions.UserError("Debe seleccionar un proveedor")
        
        try:
            # Obtener productos a importar
            products = self._get_filtered_products()
            
            if not products:
                raise exceptions.UserError("No se encontraron productos para importar")
            
            # Procesar productos
            processed = self.supplier_integration_id._process_products(products)
            
            # Actualizar estadísticas
            self.supplier_integration_id.write({
                'products_imported': self.supplier_integration_id.products_imported + processed,
                'last_import': fields.Datetime.now(),
                'last_sync_status': 'success'
            })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Importación Completada',
                    'message': f"Se importaron {processed} productos exitosamente",
                    'type': 'success',
                }
            }
            
        except Exception as e:
            self.supplier_integration_id.last_sync_status = 'error'
            raise exceptions.UserError(f"Error en importación: {str(e)}")