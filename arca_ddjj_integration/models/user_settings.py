from odoo import models, fields, api
from . import comprobante_arca
from . import user_settings  
import requests
from odoo.exceptions import UserError
from datetime import datetime
from odoo.fields import Datetime  



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
    fecha_ultimo_reset = fields.Datetime(string="FechaC último reset", readonly=True)
    
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
            
    def action_actualizar_consultas_disponibles(self):
        self.ensure_one()
        if not self.email or not self.api_key:
            raise UserError("Debés configurar el email y la API Key para consultar.")

        url = f"https://api-bot-mc.mrbot.com.ar/api/v1/users/consultas/{self.email}"
        headers = {
            "x-api-key": self.api_key,
            "Accept": "application/json"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            self.consultas_disponibles = data.get("consultas_disponibles", 0)
            iso_string = data["fecha_ultimo_reset"]
            self.fecha_ultimo_reset = datetime.fromisoformat(iso_string)
        else:
            raise UserError(f"No se pudo obtener la información de consultas. Error: {response.text}")
            
    @api.model
    def create(self, vals):
        if self.env['arca.settings'].search_count([]) >= 1:
            raise UserError("Ya existe una configuración ARCA. No se pueden crear múltiples.")
        return super().create(vals)

