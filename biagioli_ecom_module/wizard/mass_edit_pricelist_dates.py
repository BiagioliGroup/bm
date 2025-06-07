from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)

class MassEditPricelistDates(models.TransientModel):
    _name = 'mass.edit.pricelist.dates'
    _description = 'Editor masivo de fechas de listas de precios'

    date_start = fields.Date("Nueva fecha de inicio")
    date_end = fields.Date("Nueva fecha de finalización")

    def apply_mass_edit(self):
        _logger.info("📥 Ejecutando apply_mass_edit")
        _logger.info(f"📅 Fecha de inicio seleccionada: {self.date_start}")
        _logger.info(f"📅 Fecha de finalización seleccionada: {self.date_end}")

        active_ids = self.env.context.get('active_ids', [])
        _logger.info(f"📌 Registros seleccionados: {active_ids}")

        items = self.env['product.pricelist.item'].browse(active_ids)
        for item in items:
            _logger.info(f"➡️ Editando item {item.id} (producto: {item.name})")
            if self.date_start:
                item.date_start = self.date_start
                _logger.info(f"✅ Fecha de inicio aplicada: {self.date_start}")
            if self.date_end:
                item.date_end = self.date_end
                _logger.info(f"✅ Fecha de fin aplicada: {self.date_end}")

        # return {
        #     'type': 'ir.actions.client',
        #     'tag': 'reload',
        # }