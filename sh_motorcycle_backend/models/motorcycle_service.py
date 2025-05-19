from odoo import models, fields, api
from odoo.exceptions import ValidationError

class MotorcycleService(models.Model):
    _name = 'motorcycle.service'
    _description = 'Servicio de Motocicleta'
    _rec_name = 'name'

    name = fields.Char('Número de Servicio', required=True, copy=False, readonly=True, 
                      default=lambda self: self.env['ir.sequence'].next_by_code('motorcycle.service.sequence') or 'Nuevo')
    motorcycle_id = fields.Many2one('motorcycle.motorcycle', string='Motocicleta', required=True)
    description = fields.Text(string='Descripción')
    labor_description = fields.Text(string='Descripción del Trabajo')
    
    service_product_ids = fields.Many2many('product.product', 'motorcycle_service_product_rel', 
        'service_id', 'product_id', string='Productos de Servicio', domain="[('type', '=', 'service')]")
    product_ids = fields.Many2many('product.product', 'motorcycle_service_consumable_rel',
        'service_id', 'product_id', string='Productos Consumibles', domain="[('type', '=', 'consu')]")
    
    currency_id = fields.Many2one('res.currency', string='Moneda', 
        default=lambda self: self.env.company.currency_id)
    total_labor_cost = fields.Monetary(string='Costo de Mano de Obra', currency_field='currency_id')
    total_parts_cost = fields.Monetary(string='Costo de Repuestos', currency_field='currency_id', compute='_compute_totals', store=True, default=0.0)
    total_service_cost = fields.Monetary(string='Costo Total', currency_field='currency_id', compute='_compute_totals', store=True, default=0.0)

    product_line_ids = fields.One2many('motorcycle.service.product.line', 'service_id', string='Líneas de Productos')
    step_ids = fields.One2many('motorcycle.service.step', 'service_id', string='Pasos del servicio')

    @api.depends('product_line_ids.subtotal', 'total_labor_cost')
    def _compute_totals(self):
        for service in self:
            total_parts = sum(line.subtotal for line in service.product_line_ids)
            service.total_parts_cost = total_parts
            service.total_service_cost = total_parts + (service.total_labor_cost or 0.0)

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

class MotorcycleServiceProductLine(models.Model):
    _name = 'motorcycle.service.product.line'
    _description = 'Línea de Producto del Servicio'

    service_id = fields.Many2one('motorcycle.service', string='Servicio', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Producto', required=True)
    quantity = fields.Float(string='Cantidad', default=1.0)
    currency_id = fields.Many2one(related='service_id.currency_id')
    price_unit = fields.Float(string='Precio Unitario', related='product_id.list_price', readonly=True)
    subtotal = fields.Monetary(string='Subtotal', compute='_compute_subtotal', store=True, currency_field='currency_id')

    @api.depends('quantity', 'price_unit')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.price_unit
