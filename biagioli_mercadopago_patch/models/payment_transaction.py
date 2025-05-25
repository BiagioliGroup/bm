from odoo import models
from werkzeug import urls
from urllib.parse import quote as url_quote
from odoo.addons.payment_mercado_pago.controllers.main import MercadoPagoController


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _mercado_pago_prepare_preference_request_payload(self):
        # Forzar base_url a HTTPS
        base_url = self.provider_id.get_base_url().replace('http://', 'https://')  # Forzado a HTTPS - Linea agrgado el 25/10/2023.
        return_url = urls.url_join(base_url, MercadoPagoController._return_url)
        sanitized_reference = url_quote(self.reference)
        webhook_url = urls.url_join(base_url, f'{MercadoPagoController._webhook_url}/{sanitized_reference}')

        return {
            'auto_return': 'all',
            'back_urls': {
                'success': return_url,
                'pending': return_url,
                'failure': return_url,
            },
            'external_reference': self.reference,
            'items': [{
                'title': self.reference,
                'quantity': 1,
                'currency_id': self.currency_id.name,
                'unit_price': self.amount,
            }],
            'notification_url': webhook_url,
            'payer': {
                'name': self.partner_name,
                'email': self.partner_email,
                'phone': {'number': self.partner_phone},
                'address': {
                    'zip_code': self.partner_zip,
                    'street_name': self.partner_address,
                },
            },
            'payment_methods': {
                'installments': 1,
            },
        }
