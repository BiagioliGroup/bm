from odoo import models, fields, api
from . import comprobante_arca
from . import user_settings  
import requests
from odoo.exceptions import UserError


class ArcaSettings(models.Model):
    _name = 'arca.settings'
    _description = 'Configuración de conexión ARCA'

    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company, required=True)
    nombre = fields.Char(string='Nombre completo', required=True)
    cuit = fields.Char(string='CUIT', required=True)
    email = fields.Char(string='Email', required=True)
    telefono = fields.Char(string='Teléfono')
    api_key = fields.Char(string='API Key', help="Copiá aquí la API Key que recibiste por correo electrónico después de crear el usuario.")
    consultas_disponibles = fields.Integer(string='Consultas disponibles', readonly=True)
    show_warning_create = fields.Boolean(compute="_compute_show_warning_create", store=True)
    
    def _compute_show_warning_create(self):
        for rec in self:
            rec.show_warning_create = not rec.id

    def action_create_user(self):
        for rec in self:
            if not rec.email:
                raise UserError("Debés completar el campo Email para crear el usuario.")

            payload = {"mail": rec.email}
            response = requests.post("https://api-bot-mc.mrbot.com.ar/api/v1/users/", json=payload)

            if response.status_code == 200:
                rec.message_post(
                    body="El usuario fue creado correctamente. Revisá tu correo electrónico para obtener la API Key."
                )
            elif response.status_code == 422:
                raise UserError("Ya existe un usuario con este mail.")
            else:
                raise UserError(f"Error al crear el usuario: {response.text}")
            
    @api.model
    def create(self, vals):
        if self.env['arca.settings'].search_count([]) >= 1:
            raise UserError("Ya existe una configuración ARCA. No se pueden crear múltiples.")
        return super().create(vals)

