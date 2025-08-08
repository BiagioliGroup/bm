# models/product_template.py
from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    supplier_integration_id = fields.Many2one('supplier.integration', 'Integración Proveedor')
    original_price = fields.Float('Precio Original Proveedor')
    import_cost = fields.Float('Costo Importación')
    last_sync_date = fields.Datetime('Última Sincronización')