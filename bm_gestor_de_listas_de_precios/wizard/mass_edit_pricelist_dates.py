from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class MassEditPricelistDates(models.TransientModel):
    _name = 'mass.edit.pricelist.dates'
    _description = 'Editor masivo de fechas de listas de precios'

    date_start = fields.Date("Nueva fecha de inicio")
    date_end = fields.Date("Nueva fecha de finalización")

    def apply_mass_edit(self):
        items = self.env['product.pricelist.item'].browse(self.env.context.get('active_ids', []))
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
    ], required=True)
    value = fields.Float(required=True)
    date_start = fields.Date(required=True)

    def apply_adjustments(self):
        active_model = self.env.context.get('active_model')
        active_ids = self.env.context.get('active_ids')

        if active_model == 'product.template':
            products = self.env['product.template'].browse(active_ids)
            for product in products:
                new_price = (
                    product.list_price * (1 + self.value / 100)
                    if self.increase_type == 'percent'
                    else product.list_price + self.value
                )
                product.with_context(skip_price_history=True).write({'list_price': new_price})

                pricelist = self.env['product.pricelist'].search([
                    ('name', '=', 'Historial precio público'),
                    ('currency_id', '=', product.currency_id.id),
                    ('company_id', '=', product.company_id.id),
                ], limit=1)
                if not pricelist:
                    pricelist = self.env['product.pricelist'].create({
                        'name': 'Historial precio público',
                        'currency_id': product.currency_id.id,
                        'company_id': product.company_id.id,
                        'selectable': False,
                    })
                self.env['product.pricelist.item'].create({
                    'pricelist_id': pricelist.id,
                    'product_tmpl_id': product.id,
                    'applied_on': '1_product',
                    'compute_price': 'fixed',
                    'fixed_price': new_price,
                    'date_start': fields.Date.today(),
                })
        else:
            items = self.env['product.pricelist.item'].browse(active_ids)
            for item in items.filtered(lambda i: i.compute_price == 'fixed'):
                new_price = (
                    item.fixed_price * (1 + self.value / 100)
                    if self.increase_type == 'percent'
                    else item.fixed_price + self.value
                )
                item.write({'date_end': self.date_start - timedelta(days=1)})
                item.copy({
                    'fixed_price': new_price,
                    'date_start': self.date_start,
                    'date_end': False
                })


class MassEditPricelistCloneAdjustment(models.TransientModel):
    _name = 'mass.edit.pricelist.clone.adjustment'
    _description = 'Clonar reglas de precios con ajuste'

    increase_type = fields.Selection([
        ('percent', 'Porcentaje'),
        ('fixed', 'Monto fijo')
    ], required=True)
    value = fields.Float(required=True)

    def apply_clone_adjustment(self):
        today = fields.Date.today()
        active_model = self.env.context.get("active_model", "")
        active_ids = self.env.context.get("active_ids", [])

        if active_model == "product.template":
            products = self.env["product.template"].browse(active_ids)
            for product in products:
                new_price = (
                    product.list_price * (1 + self.value / 100)
                    if self.increase_type == "percent"
                    else product.list_price + self.value
                )
                product.with_context(skip_price_history=True).write({'list_price': new_price})

                pricelist = self.env["product.pricelist"].search([
                    ("name", "=", "Historial precio público"),
                    ("currency_id", "=", product.currency_id.id),
                    ("company_id", "=", product.company_id.id),
                ], limit=1)

                if not pricelist:
                    pricelist = self.env["product.pricelist"].create({
                        "name": "Historial precio público",
                        "currency_id": product.currency_id.id,
                        "company_id": product.company_id.id,
                        "selectable": False,
                    })

                self.env["product.pricelist.item"].create({
                    "pricelist_id": pricelist.id,
                    "product_tmpl_id": product.id,
                    "applied_on": "1_product",
                    "compute_price": "fixed",
                    "fixed_price": new_price,
                    "date_start": today,
                    "date_end": False,
                })

        else:
            items = self.env["product.pricelist.item"].browse(active_ids)
            for item in items.filtered(lambda i: i.compute_price == 'fixed'):
                new_price = (
                    item.fixed_price * (1 + self.value / 100)
                    if self.increase_type == "percent"
                    else item.fixed_price + self.value
                )
                item.write({"date_end": today})
                item.copy({
                    "fixed_price": new_price,
                    "date_start": today,
                    "date_end": False
                })


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def write(self, vals):
        # Cierre de historial incluso si no vamos a crear uno nuevo
        skip_history = self.env.context.get('skip_price_history', False)
        res = super().write(vals)

        if 'list_price' in vals:
            for template in self:
                new_start = datetime.now()
                company = template.company_id or self.env.company

                historial_pricelist = self.env['product.pricelist'].search([
                    ('name', '=', 'Historial precio público'),
                    ('currency_id', '=', template.currency_id.id),
                    ('company_id', '=', company.id),
                ], limit=1)

                if historial_pricelist:
                    last_item = self.env['product.pricelist.item'].search([
                        ('pricelist_id', '=', historial_pricelist.id),
                        ('product_tmpl_id', '=', template.id),
                        ('date_end', '=', False)
                    ], order='date_start desc', limit=1)

                    if last_item:
                        safe_end = new_start - timedelta(seconds=1)
                        if last_item.date_start < safe_end:
                            last_item.date_end = safe_end
                        else:
                            last_item.date_end = last_item.date_start + timedelta(seconds=1)
                            new_start = last_item.date_end + timedelta(seconds=1)

                # Solo si no es ajuste desde wizard, guardamos nuevo item
                if not skip_history:
                    if not historial_pricelist:
                        historial_pricelist = self.env['product.pricelist'].create({
                            'name': 'Historial precio público',
                            'currency_id': template.currency_id.id,
                            'company_id': company.id,
                            'selectable': False,
                        })

                    self.env['product.pricelist.item'].create({
                        'pricelist_id': historial_pricelist.id,
                        'product_tmpl_id': template.id,
                        'applied_on': '1_product',
                        'compute_price': 'fixed',
                        'fixed_price': vals['list_price'],
                        'date_start': new_start,
                        'date_end': False
                    })

        return res
