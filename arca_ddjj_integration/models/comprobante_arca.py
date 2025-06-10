from odoo import models, fields, api

class ComprobanteArca(models.Model):
    _name = 'comprobante.arca'
    _description = 'Comprobante descargado desde ARCA'

    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company, required=True)
    cuit_emisor = fields.Char(string='CUIT Emisor')
    razon_social_emisor = fields.Char(string='Razón Social Emisor')
    fecha_emision = fields.Date(string='Fecha de Emisión')
    tipo_comprobante = fields.Char(string='Tipo Comprobante')
    nro_comprobante = fields.Char(string='Número de Comprobante')
    importe_total = fields.Monetary(
        string='Importe Total',
        currency_field='moneda_id'
    )
    moneda_id = fields.Many2one('res.currency', string='Moneda', default=lambda self: self.env.company.currency_id)
    estado_coincidencia = fields.Selection([
        ('coincide', 'Coincide con Odoo'),
        ('solo_arca', 'Solo en ARCA'),
        ('solo_odoo', 'Solo en Odoo'),
    ], string='Estado de coincidencia', default='solo_arca')
    incluir_en_ddjj = fields.Boolean(string='¿Incluir en DDJJ?', default=True)

from odoo import models, fields, api
import requests

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
        """Crear usuario en la API de ARCA"""
        for rec in self:
            payload = {
                "name": rec.nombre,
                "cuit": rec.cuit,
                "email": rec.email,
                "telefono": rec.telefono
            }
            response = requests.post("https://api-bot-mc.mrbot.com.ar/api/v1/users/", json=payload)
            if response.status_code == 200:
                data = response.json()
                rec.api_key = data.get("api_key", "")
            else:
                raise UserError("Error al crear usuario: %s" % response.text)

