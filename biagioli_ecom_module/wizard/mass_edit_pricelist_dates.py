from odoo import models, fields, tools
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime, time
import pytz
import logging

_logger = logging.getLogger(__name__)


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

        # Detectar zona horaria del usuario (si está definida en la sesión)
        user_tz = self.env.user.tz or 'UTC'
        tz = pytz.timezone(user_tz)
        _logger.info(f"🌐 Zona horaria del usuario: {user_tz}")

        # Convertir la fecha al comienzo del día en su zona horaria local
        local_dt = tz.localize(datetime.combine(self.date_start, time.min))
        # Convertir de vuelta a fecha pura en UTC (eliminando desfase)
        corrected_date_start = local_dt.astimezone(pytz.utc).date()

        active_ids = self.env.context.get('active_ids', [])
        items = self.env['product.pricelist.item'].browse(active_ids)

        for item in items:
            if item.compute_price != 'fixed':
                continue

            if self.increase_type == 'percent':
                new_price = item.fixed_price * (1 + self.value / 100)
            else:
                new_price = item.fixed_price + self.value

            item.write({
                'fixed_price': new_price,
                'date_start': corrected_date_start,
                'date_end': False
            })
