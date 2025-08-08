# models/res_partner.py
from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    # Integración API
    has_api_integration = fields.Boolean('Tiene Integración API', 
                                       help="Indica si este proveedor tiene integración API configurada")
    integration_ids = fields.One2many('supplier.integration', 'partner_id', 'Integraciones')
    integration_count = fields.Integer('Cantidad Integraciones', compute='_compute_integration_count')
    
    # Campos específicos para APIs (se muestran solo si has_api_integration=True)
    api_base_url = fields.Char('URL Base API', help="URL base del API del proveedor")
    api_token = fields.Char('Token API', help="Token de autenticación")
    api_version = fields.Char('Versión API', default='v4')
    
    # Configuración de importación
    default_markup_percentage = fields.Float('Markup % por Defecto', default=25.0,
                                           help="Porcentaje de markup para productos de este proveedor")
    default_import_cost_percentage = fields.Float('Costo Importación % por Defecto', default=15.0,
                                                 help="Porcentaje de costo de importación")
    
    # Información de país para costos de importación
    import_country_id = fields.Many2one('res.country', 'País de Importación',
                                      help="País desde donde se importan los productos")
    requires_import = fields.Boolean('Requiere Importación', 
                                   help="Los productos de este proveedor requieren importación")
    
    @api.depends('integration_ids')
    def _compute_integration_count(self):
        for partner in self:
            partner.integration_count = len(partner.integration_ids)
    
    def action_create_integration(self):
        """Acción para crear nueva integración desde el proveedor"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Nueva Integración - {self.name}',
            'res_model': 'supplier.integration',
            'view_mode': 'form',
            'context': {
                'default_partner_id': self.id,
                'default_api_base_url': self.api_base_url,
                'default_api_token': self.api_token,
                'default_api_version': self.api_version,
                'default_markup_percentage': self.default_markup_percentage,
                'default_import_cost_percentage': self.default_import_cost_percentage,
            },
            'target': 'current',
        }
    
    def action_view_integrations(self):
        """Ver todas las integraciones de este proveedor"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Integraciones - {self.name}',
            'res_model': 'supplier.integration',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }
    
    def sync_all_integrations(self):
        """Sincronizar todas las integraciones de este proveedor"""
        if not self.integration_ids:
            raise exceptions.UserError("Este proveedor no tiene integraciones configuradas")
        
        total_synced = 0
        errors = []
        
        for integration in self.integration_ids.filtered('is_active'):
            try:
                result = integration.sync_products()
                total_synced += integration.products_imported
            except Exception as e:
                errors.append(f"{integration.integration_type}: {str(e)}")
        
        if errors:
            message = f"Sincronización completada con errores:\n" + "\n".join(errors)
            message_type = 'warning'
        else:
            message = f"Sincronización exitosa. {total_synced} productos procesados."
            message_type = 'success'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Sincronización Completada',
                'message': message,
                'type': message_type,
            }
        }
    
    @api.model
    def create(self, vals):
        """Al crear proveedor, detectar automáticamente si requiere importación"""
        partner = super().create(vals)
        
        # Si tiene país y no es Argentina, probablemente requiere importación
        if partner.country_id and partner.country_id.code != 'AR' and partner.supplier_rank > 0:
            partner.requires_import = True
            partner.import_country_id = partner.country_id.id
        
        return partner