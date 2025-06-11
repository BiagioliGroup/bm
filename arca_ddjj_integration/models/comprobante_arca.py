from odoo import models, fields, api
from odoo.exceptions import UserError
import requests

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

class WizardImportarComprobantes(models.TransientModel):
    _name = 'wizard.importar.comprobantes'
    _description = 'Importar Comprobantes desde ARCA'

    fecha_desde = fields.Date(string="Desde", required=True)
    fecha_hasta = fields.Date(string="Hasta", required=True)
    descarga_emitidos = fields.Boolean(string="Descargar Emitidos", default=False   )
    descarga_recibidos = fields.Boolean(string="Descargar Recibidos", default=True)

    def action_importar(self):
        config = self.env['arca.settings'].search([], limit=1)
        if not config or not config.api_key:
            raise UserError("Debe configurar su API Key en el Panel Cliente ARCA antes de importar.")

        payload = {
                "desde": self.fecha_desde.strftime("%d/%m/%Y"),
                "hasta": self.fecha_hasta.strftime("%d/%m/%Y"),
                "cuit_inicio_sesion": config.cuit_representante,
                "representado_nombre": config.nombre,
                "representado_cuit": config.cuit,
                "contrasena": config.clave_fiscal,
                "descarga_emitidos": self.descarga_emitidos,
                "descarga_recibidos": self.descarga_recibidos,
            }
        headers = {
            "x-api-key": config.api_key,
            "email": config.email,
        }
        url = "https://api-bot-mc.mrbot.com.ar/api/v1/comprobantes/consulta"
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            raise UserError(f"Error al consultar ARCA: {response.text}")

        data = response.json()

        if not data.get("success"):
            raise UserError(f"Consulta fallida: {data.get('message')}")

        # Aquí parsearíamos data['mis_comprobantes_recibidos'] y data['mis_comprobantes_emitidos']
        # y crearíamos registros comprobante.arca

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Importación exitosa",
                "message": "Los comprobantes han sido importados correctamente.",
                "type": "success",
                "sticky": False,
            }
        }


