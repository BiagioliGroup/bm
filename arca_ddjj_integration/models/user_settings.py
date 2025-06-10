from odoo import models, fields, api
from . import comprobante_arca
from . import user_settings  


class ArcaSettings(models.Model):
    _name = 'arca.settings'
    _description = 'Configuración de conexión ARCA'

    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company, required=True)
    nombre = fields.Char(string='Nombre completo', required=True)
    cuit = fields.Char(string='CUIT', required=True)
    email = fields.Char(string='Email', required=True)
    telefono = fields.Char(string='Teléfono')
    api_key = fields.Char(string='API Key', readonly=True)
    consultas_disponibles = fields.Integer(string='Consultas disponibles', readonly=True)

    def action_create_user(self):
        for rec in self:
            if not rec.email:
                raise UserError("Debés completar el campo Email para crear el usuario.")
            payload = {"mail": rec.email}
            response = requests.post("https://api-bot-mc.mrbot.com.ar/api/v1/users/", json=payload)
            if response.status_code == 200:
                data = response.json()
                rec.api_key = data.get("data", {}).get("api_key", "")
            else:
                raise UserError(f"Error al crear usuario: {response.text}")
            
    @api.model
    def create(self, vals):
        if self.env['arca.settings'].search_count([]) >= 1:
            raise UserError("Ya existe una configuración ARCA. No se pueden crear múltiples.")
        return super().create(vals)

