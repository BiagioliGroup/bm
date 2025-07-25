# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
import logging

_logger = logging.getLogger(__name__)

class WebsiteSaleDebug(WebsiteSale):

    def _check_addresses(self, order_sudo):
        # 1) Volcar los datos actuales de invoice/shipping
        try:
            inv = order_sudo.partner_invoice_id.read(['id', 'street', 'city', 'zip', 'country_id'])[0]
            shp = order_sudo.partner_shipping_id.read(['id', 'street', 'city', 'zip', 'country_id'])[0]
        except Exception as e:
            _logger.error("🛠️  Error leyendo partner_invoice/shipping: %s", e)
            inv, shp = {}, {}
        _logger.info("🛠️  CHECK ADDRESSES: invoice=%s, shipping=%s", inv, shp)

        # 2) Compruebo si es carrito anónimo
        if order_sudo._is_anonymous_cart():
            _logger.info("   ➡️  Carrito anónimo -> redirigir a /shop/address")
            return request.redirect('/shop/address')

        # 3) Delivery
        delivery_partner = order_sudo.partner_shipping_id
        ok_ship = self._check_delivery_address(delivery_partner)
        _logger.info("   Delivery complete? %s (partner %s)", ok_ship, delivery_partner.id)
        if not ok_ship and delivery_partner._can_be_edited_by_current_customer(order_sudo, 'delivery'):
            _logger.info("   ➡️  Delivery insuficiente, partner=%s", delivery_partner.id)
            return request.redirect(
                f'/shop/address?partner_id={delivery_partner.id}&address_type=delivery'
            )

        # 4) Billing
        invoice_partner = order_sudo.partner_invoice_id
        ok_bill = self._check_billing_address(invoice_partner)
        _logger.info("   Billing complete?  %s (partner %s)", ok_bill, invoice_partner.id)
        if not ok_bill and invoice_partner._can_be_edited_by_current_customer(order_sudo, 'billing'):
            _logger.info("   ➡️  Billing insuficiente, partner=%s", invoice_partner.id)
            return request.redirect(
                f'/shop/address?partner_id={invoice_partner.id}&address_type=billing'
            )

        # 5) Si todo OK, no redirección
        _logger.info("   ✅ Direcciones OK, continuamos checkout")
        return None
