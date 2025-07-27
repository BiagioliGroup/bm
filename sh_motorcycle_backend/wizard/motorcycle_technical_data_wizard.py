# models/motorcycle_technical_data_wizard.py
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class MotorcycleTechnicalDataWizard(models.TransientModel):
    _name = 'motorcycle.technical.data.wizard'
    _description = 'Wizard para cargar Datos Técnicos en lote'

    motorcycle_ids = fields.Many2many(
        'motorcycle.motorcycle',
        string='Motocicletas',
        required=True,
    )
    category_id = fields.Many2one(
        'product.category',
        string='Categoría',
        required=True,
    )
    attribute_id = fields.Many2one(
        'product.attribute',
        string='Atributo',
        required=True,
    )
    value_id = fields.Many2one(
        'product.attribute.value',
        string='Valor',
        required=True,
    )
    note = fields.Char(string='Nota Adicional')

    @api.onchange('category_id')
    def _onchange_category(self):
        if self.category_id:
            return {'domain': {
                'attribute_id': [('categ_ids', 'in', [self.category_id.id])]
            }}
        return {}

    @api.onchange('attribute_id')
    def _onchange_attribute(self):
        if self.attribute_id:
            return {'domain': {
                'value_id': [('attribute_id', '=', self.attribute_id.id)]
            }}
        return {}

    def action_apply(self):
        if not self.motorcycle_ids:
            raise UserError(_("Debe seleccionar al menos una motocicleta."))
        data_obj = self.env['motorcycle.technical.data']
        for moto in self.motorcycle_ids:
            data_obj.create({
                'motorcycle_id': moto.id,
                'category_id':   self.category_id.id,
                'attribute_id':  self.attribute_id.id,
                'value_id':      self.value_id.id,
                'note':          self.note,
            })
        return {'type': 'ir.actions.act_window_close'}
