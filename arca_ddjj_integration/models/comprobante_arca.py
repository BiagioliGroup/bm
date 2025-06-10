from odoo import models, fields, api
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



