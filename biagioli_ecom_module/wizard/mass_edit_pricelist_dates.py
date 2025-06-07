from odoo import models, fields
import logging


_logger = logging.getLogger(__name__)


class MassEditPricelistDates(models.TransientModel):
    _name = 'mass.edit.pricelist.dates'
    _description = 'Editor masivo de fechas de listas de precios'

    date_start = fields.Date("Nueva fecha de inicio")
    date_end = fields.Date("Nueva fecha de finalización")

    def apply_mass_edit(self):

        active_ids = self.env.context.get('active_ids', [])

        items = self.env['product.pricelist.item'].browse(active_ids)
        for item in items:
            if self.date_start:
                item.date_start = self.date_start
            if self.date_end:
                item.date_end = self.date_end

    
class MassEditPricelistAdjustment(models.TransientModel):
    _name = 'mass.edit.pricelist.adjustment'
    _description = 'Ajuste masivo de precios'

    increase_type = fields.Selection([
        ('percent', 'Porcentaje'),
        ('fixed', 'Monto fijo')
    ], string='Tipo de aumento', required=True)
    value = fields.Float('Valor del aumento', required=True)
    date_start = fields.Date('Fecha de inicio', required=True)

    def apply_adjustment(self):
        _logger.info("🛠 Aplicando ajustes de precio")

        active_ids = self.env.context.get('active_ids', [])
        items = self.env['product.pricelist.item'].browse(active_ids)

        for item in items:
            if item.compute_price != 'fixed':
                continue  # ignorar dinámicos

            if self.increase_type == 'percent':
                new_price = item.fixed_price * (1 + self.value / 100)
            else:
                new_price = item.fixed_price + self.value

            item.write({
                'fixed_price': new_price,
                'date_start': self.date_start,
                'date_end': False
            })
