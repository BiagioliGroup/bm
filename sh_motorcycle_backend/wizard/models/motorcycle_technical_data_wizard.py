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

    @api.onchange('category_id', 'attribute_id')
    def _onchange_category_attribute(self):
        """Actualizar dominio de motorcycle_ids: excluir aquellas motos
        que ya tengan un dato técnico con la misma categoría+atributo."""
        if not (self.category_id and self.attribute_id):
            # si falta algo, no forzamos nada
            return {'domain': {'motorcycle_ids': []}}
        # buscar todas las motos que ya tengan un record técnico para esta cat+attr
        Technical = self.env['motorcycle.technical.data']
        used = Technical.search([
            ('category_id', '=', self.category_id.id),
            ('attribute_id', '=', self.attribute_id.id),
        ]).mapped('motorcycle_id.id')
        # domain: id not in used
        return {
            'domain': {
                'motorcycle_ids': [('id', 'not in', used or [0])]
            }
        }

    def action_apply(self):
        """Al pulsar 'Aplicar', crea un registro técnico por cada moto seleccionada."""
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
