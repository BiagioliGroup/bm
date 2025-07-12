from odoo import models, fields


class CashflowProjection(models.Model):
    _name = 'cashflow.projection'
    _description = 'Proyección de Cashflow'

    name = fields.Char(string="Concepto")
    partner_id = fields.Many2one('res.partner', string="Contacto")
    date = fields.Date(string="Fecha")
    amount = fields.Float(string="Importe")
    currency_id = fields.Many2one('res.currency', string="Moneda", default=lambda self: self.env.company.currency_id)
    type = fields.Selection([
        ('ingreso', 'Ingreso'),
        ('egreso', 'Egreso')
    ], string="Tipo", required=True)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('confirmed', 'Confirmado'),
        ('done', 'Realizado')
    ], string="Estado", default='draft')