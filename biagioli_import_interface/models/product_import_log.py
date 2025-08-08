# models/product_import_log.py
from odoo import models, fields

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