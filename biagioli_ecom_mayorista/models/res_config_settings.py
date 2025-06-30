from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pricelist_ids_show = fields.Many2many(
        'product.pricelist',
        'res_config_settings_pricelist_ids_rel',
        'config_id', 'pricelist_id',
        string='Listas de precios visibles en tienda',
    )

    show_user_pricelist_badge = fields.Boolean(
        string="Mostrar nombre de lista de precios en el header",
        config_parameter='biagioli_ecom_mayorista.show_user_pricelist_badge',
    )

    show_comparative_prices = fields.Boolean(
        string="Mostrar precios comparativos",
        config_parameter="biagioli_ecom_mayorista.show_comparative_prices"
    )

    show_ribbon_by_supplier = fields.Boolean(
        string="Mostrar cintas por proveedor",
        config_parameter="biagioli_ecom_mayorista.show_ribbon_by_supplier"
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        Pricelist = self.env['product.pricelist']
        param = self.env['ir.config_parameter'].sudo().get_param('biagioli_ecom_mayorista.pricelist_ids_show')
        ids = [int(x) for x in param.split(',')] if param else []
        res.update(
            pricelist_ids_show=[(6, 0, ids)]
        )
        return res

    def set_values(self):
        super().set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'biagioli_ecom_mayorista.pricelist_ids_show',
            ','.join(str(x.id) for x in self.pricelist_ids_show)
        )
