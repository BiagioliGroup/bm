from odoo import models, fields, api
from . import comprobante_arca
from . import user_settings  
import requests
from odoo.exceptions import UserError
from datetime import datetime



class ArcaSettings(models.Model):
    _name = 'arca.settings'
    _description = 'Configuración de conexión ARCA'

    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company, required=True)
    nombre = fields.Char(string='Nombre del Representado', required=True)
    cuit = fields.Char(string='CUIT del Representado', required=True)
    cuit_representante = fields.Char(string='CUIT del Representante')
    clave_fiscal = fields.Char(string='Clave fiscal')
    email = fields.Char(string='Email', required=True)
    telefono = fields.Char(stsring='Teléfono')
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
                raise UserError("El usuario fue creado correctamente. Revisá tu correo electrónico para obtener la API Key.")

            elif response.status_code == 422:
                raise UserError("Ya existe un usuario con este mail.")
            else:
                raise UserError(f"Error al crear el usuario: {response.text}")
            
    def actualizar_consultas_disponibles(self):
        for rec in self:
            if not rec.email:
                raise UserError("Falta el email para consultar la disponibilidad.")
            url = f"https://api-bot-mc.mrbot.com.ar/api/v1/users/consultas/{rec.email}"
            headers = {
                "x-api-key": rec.api_key,
                "email": rec.email,
            }
            response = requests.get(url, headers=headers)

            if response.status_code != 200:
                raise UserError(f"Error al consultar las consultas disponibles: {response.text}")
            
            data = response.json()
            rec.consultas_disponibles = data.get("consultas_disponibles", 0)
            fecha = data.get("fecha_ultimo_reset")
            if fecha:
                try:
                    rec.fecha_ultimo_reset = datetime.strptime(fecha, "%Y-%m-%dT%H:%M:%S.%fZ")
                except Exception:
                    rec.fecha_ultimo_reset = False
            
    @api.model
    def create(self, vals):
        if self.env['arca.settings'].search_count([]) >= 1:
            raise UserError("Ya existe una configuración ARCA. No se pueden crear múltiples.")
        return super().create(vals)

