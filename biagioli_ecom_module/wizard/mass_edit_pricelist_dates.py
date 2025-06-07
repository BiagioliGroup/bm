from odoo import models, fields, tools, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime, time
from datetime import date
import pytz
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

    class MassEditPricelistCloneAdjustment(models.TransientModel):
        _name = 'mass.edit.pricelist.clone.adjustment'
        _description = 'Clonar reglas de precios con ajuste'

        increase_type = fields.Selection([
            ('percent', 'Porcentaje'),
            ('fixed', 'Monto fijo')
        ], string='Tipo de aumento', required=True)
        value = fields.Float('Valor del aumento', required=True)

        def apply_clone_adjustment(self):
            today = fields.Date.today()
            active_ids = self.env.context.get('active_ids', [])
            items = self.env['product.pricelist.item'].browse(active_ids)

            for item in items:
                if item.compute_price != 'fixed':
                    continue

                # Calcular nuevo precio
                if self.increase_type == 'percent':
                    new_price = item.fixed_price * (1 + self.value / 100)
                else:
                    new_price = item.fixed_price + self.value

                # Cerrar regla actual
                item.write({'date_end': today})

                # Crear nueva regla clonada
                item.copy({
                    'fixed_price': new_price,
                    'date_start': today,
                    'date_end': False,
                })

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def write(self, vals):
        res = super().write(vals)

        if 'list_price' in vals:
            for template in self:
                historial_pricelist = self.env['product.pricelist'].search([
                    ('name', '=', 'Historial precio público'),
                    ('currency_id', '=', template.currency_id.id),
                    ('company_id', 'in', [template.company_id.id, False])
                ], limit=1)

                if not historial_pricelist:
                    historial_pricelist = self.env['product.pricelist'].create({
                        'name': 'Historial precio público',
                        'currency_id': template.currency_id.id,
                        'company_id': template.company_id.id,
                    })

                # Obtener fecha actual
                now = datetime.now()

                # Buscar el último registro sin fecha de fin
                last_item = self.env['product.pricelist.item'].search([
                    ('pricelist_id', '=', historial_pricelist.id),
                    ('product_tmpl_id', '=', template.id),
                    ('date_end', '=', False)
                ], order='date_start desc', limit=1)

                if last_item:
                    # Cierra el último registro justo antes del nuevo
                    last_item.date_end = now - timedelta(seconds=1)

                # Crear el nuevo registro con el nuevo precio
                self.env['product.pricelist.item'].create({
                    'pricelist_id': historial_pricelist.id,
                    'product_tmpl_id': template.id,
                    'applied_on': '1_product',
                    'compute_price': 'fixed',
                    'fixed_price': vals['list_price'],
                    'date_start': now,
                    'date_end': False
                })

        return res