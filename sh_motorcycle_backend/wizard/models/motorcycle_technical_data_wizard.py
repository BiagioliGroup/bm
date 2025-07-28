# sh_motorcycle_backend/wizard/motorcycle_technical_data_wizard.py
from odoo import api, fields, models

class MotorcycleTechnicalDataWizard(models.TransientModel):
    _name = 'motorcycle.technical.data.wizard'
    _description = 'Wizard para cargar Datos Técnicos en lote'

    category_id     = fields.Many2one('product.category',       string='Categoría', required=True)
    attribute_id    = fields.Many2one('product.attribute',     string='Atributo',  required=True)
    value_id        = fields.Many2one('product.attribute.value',string='Valor',     required=True)
    note            = fields.Char(                              string='Nota Adicional')
    motorcycle_ids  = fields.Many2many(
        'motorcycle.motorcycle', 
        string='Motocicletas',
        help="Selecciona sólo las motos que aún no tengan un dato técnico para Cat+Atr."
    )

    @api.onchange('category_id', 'attribute_id')
    def _onchange_cat_attr(self):
        # cuando cambian categoría o atributo, recalculemos qué motos ya tienen dato
        if not (self.category_id and self.attribute_id):
            return {'domain': {'motorcycle_ids': []}}
        # buscar todos los registros ya creados para esta cat+atr
        used = self.env['motorcycle.technical.data'].search([
            ('category_id', '=', self.category_id.id),
            ('attribute_id','=', self.attribute_id.id),
        ]).mapped('motorcycle_id').ids
        return {
            'domain': {
                # excluir las motos que ya aparezcan en used
                'motorcycle_ids': [('id', 'not in', used)]
            },
            # además, limpiamos la selección previa por si cambió
            'value': {
                'motorcycle_ids': False
            }
        }

    def action_apply(self):
        # crea sólo para las motos que quedaron seleccionadas
        to_create = []
        for moto in self.motorcycle_ids:
            to_create.append({
                'motorcycle_id': moto.id,
                'category_id':  self.category_id.id,
                'attribute_id': self.attribute_id.id,
                'value_id':     self.value_id.id,
                'note':         self.note,
            })
        if to_create:
            self.env['motorcycle.technical.data'].create(to_create)
        return {'type': 'ir.actions.act_window_close'}
