# sh_motorcycle_backend/wizard/motorcycle_technical_data_wizard.py
from odoo import api, fields, models

class MotorcycleTechnicalDataWizard(models.TransientModel):
    _name = 'motorcycle.technical.data.wizard'
    _description = 'Wizard para cargar Datos Técnicos en lote'

    category_id = fields.Many2one(
        'product.category', string='Categoría', required=True,
        help="Categoría del dato técnico."
    )
    attribute_id = fields.Many2one(
        'product.attribute', string='Atributo', required=True,
        help="Atributo dentro de la categoría."
    )
    value_id = fields.Many2one(
        'product.attribute.value', string='Valor', required=True,
        help="Valor del atributo."
    )
    note = fields.Char(string='Nota Adicional')

    motorcycle_ids = fields.Many2many(
        'motorcycle.motorcycle', string='Motocicletas',
        help="Selecciona las motocicletas a las que se aplicará este dato."
    )

    used_moto_ids  = fields.Many2many(
        'motorcycle.motorcycle', string='Motos ya usadas',
        compute='_compute_used_motos'
    )


    @api.depends('category_id', 'attribute_id')
    def _compute_used_motos(self):
        """Recupera las motos que YA tienen un registro técnico con cat+attr dados."""
        Technical = self.env['motorcycle.technical.data']
        for wiz in self:
            if wiz.category_id and wiz.attribute_id:
                used = Technical.search([
                    ('category_id', '=', wiz.category_id.id),
                    ('attribute_id', '=', wiz.attribute_id.id),
                ]).mapped('motorcycle_id.id')
            else:
                used = []
            wiz.used_moto_ids = [(6, 0, used)]

    def action_apply(self):
        """Crea un dato técnico por cada moto nueva."""
        Technical = self.env['motorcycle.technical.data']
        for moto in self.motorcycle_ids:
            Technical.create({
                'motorcycle_id': moto.id,
                'category_id':    self.category_id.id,
                'attribute_id':   self.attribute_id.id,
                'value_id':       self.value_id.id,
                'note':           self.note,
            })
        return {'type': 'ir.actions.act_window_close'}
