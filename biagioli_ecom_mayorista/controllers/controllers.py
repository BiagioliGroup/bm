from odoo.http import request

@http.route('/', type='http', auth="public", website=True)
def homepage(**kwargs):
    show_badge = request.env['ir.config_parameter'].sudo().get_param(
        'biagioli_ecom_mayorista.show_user_pricelist_badge', default='False'
    ) == 'True'
    values = {
        'show_user_pricelist_badge': show_badge,
    }
    return request.render('website.homepage', values)
