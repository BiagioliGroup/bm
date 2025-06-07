from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, time, timedelta
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
    ], required=True)
    value = fields.Float(required=True)
    date_start = fields.Date(required=True)

    def apply_adjustment(self):
        user_tz = self.env.user.tz or 'UTC'
        tz = pytz.timezone(user_tz)
        local_dt = tz.localize(datetime.combine(self.date_start, time.min))
        corrected_date_start = local_dt.astimezone(pytz.utc).date()

        items = self.env['product.pricelist.item'].browse(self.env.context.get('active_ids', []))
        for item in items.filtered(lambda i: i.compute_price == 'fixed'):
            new_price = item.fixed_price * (1 + self.value / 100) if self.increase_type == 'percent' else item.fixed_price + self.value
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
    ], required=True)
    value = fields.Float(required=True)

    def apply_clone_adjustment(self):
        today = fields.Date.today()
        items = self.env['product.pricelist.item'].browse(self.env.context.get('active_ids', []))
        for item in items.filtered(lambda i: i.compute_price == 'fixed'):
            new_price = item.fixed_price * (1 + self.value / 100) if self.increase_type == 'percent' else item.fixed_price + self.value
            item.write({'date_end': today})
            item.copy({'fixed_price': new_price, 'date_start': today, 'date_end': False})


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    # Ya no necesita lógica en write()


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def write(self, vals):
        res = super().write(vals)
        if 'list_price' in vals:
            now = datetime.now()
            for product in self:
                template = product.product_tmpl_id
                company = template.company_id or self.env.company
                if len(self.env.companies) > 1 and not company:
                    raise UserError(_("Debe seleccionar una sola empresa antes de realizar la creación del precio."))

                country = company.country_id
                all_groups = self.env['res.country.group'].search([])
                country_group = all_groups.filtered(lambda g: g.country_ids == country)

                pricelist = self.env['product.pricelist'].search([
                    ('name', '=', 'Historial precio público'),
                    ('currency_id', '=', template.currency_id.id),
                    ('company_id', '=', company.id),
                ], limit=1)

                if not pricelist:
                    pricelist = self.env['product.pricelist'].create({
                        'name': 'Historial precio público',
                        'currency_id': template.currency_id.id,
                        'company_id': company.id,
                        'country_group_ids': [(6, 0, [country_group.id])] if country_group else False,
                        'selectable': False,
                        'website_id': False,
                    })

                last_item = self.env['product.pricelist.item'].search([
                    ('pricelist_id', '=', pricelist.id),
                    ('product_tmpl_id', '=', template.id),
                    ('date_end', '=', False)
                ], order='date_start desc', limit=1)

                if last_item:
                    safe_end = now - timedelta(seconds=1)
                    if last_item.date_start < safe_end:
                        last_item.date_end = safe_end
                    else:
                        now = last_item.date_start + timedelta(seconds=2)
                        last_item.date_end = last_item.date_start + timedelta(seconds=1)

                self.env['product.pricelist.item'].create({
                    'pricelist_id': pricelist.id,
                    'product_tmpl_id': template.id,
                    'applied_on': '1_product',
                    'compute_price': 'fixed',
                    'fixed_price': vals['list_price'],
                    'date_start': now,
                    'date_end': False
                })
        return res
