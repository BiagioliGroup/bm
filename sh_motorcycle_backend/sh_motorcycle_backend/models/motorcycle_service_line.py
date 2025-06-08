from odoo import models, fields, api

class MotorcycleServiceLine(models.Model):
    _name = 'motorcycle.service.line'
    _description = 'Línea del Servicio de Motocicleta'
    _order = 'sequence, id'
    
    service_id = fields.Many2one('motorcycle.service', string='Servicio de moto', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Secuencia', default=10)
    display_type = fields.Selection([
        ('line', 'Producto'),
        ('section', 'Sección'),
        ('note', 'Nota'),
    ], string='Tipo de línea', default='line', required=True)
    product_id = fields.Many2one('product.product', string='Producto')
    name = fields.Text(string='Descripción')
    quantity = fields.Float(string='Cantidad', default=1.0)
    price_unit = fields.Float(string='Precio unitario')
    subtotal = fields.Monetary(string='Subtotal', compute='_compute_subtotal', store=True, currency_field='currency_id')
    currency_id = fields.Many2one(related='service_id.currency_id')

    @api.depends('display_type', 'quantity', 'price_unit')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.price_unit if line.display_type == 'line' else 0.0

    def add_line_product(self):
        self.ensure_one()
        self.env['motorcycle.service.line'].create({
            'service_id': self.id,
            'display_type': 'line',
            'name': '',
            'quantity': 1,
            'price_unit': 0,
        })

    def add_line_section(self):
        self.ensure_one()
        self.env['motorcycle.service.line'].create({
            'service_id': self.id,
            'display_type': 'section',
            'name': 'Nueva sección',
        })

    def add_line_note(self):
        self.ensure_one()
        self.env['motorcycle.service.line'].create({
            'service_id': self.id,
            'display_type': 'note',
            'name': 'Nueva nota',
        })


class MotorcycleServiceStep(models.Model):
    _name = 'motorcycle.service.step'
    _description = 'Paso operativo del servicio técnico'
    _order = 'sequence, id'

    service_id = fields.Many2one('motorcycle.service', string='Servicio de moto', required=True, ondelete='cascade')
    name = fields.Char('Descripción del paso', required=True)
    is_done = fields.Boolean('Completado')
    note = fields.Text('Nota o instrucción especial')
    pdf_file = fields.Binary('Archivo PDF', attachment=True)
    pdf_filename = fields.Char('Nombre del archivo')
    sequence = fields.Integer('Secuencia', default=10)
