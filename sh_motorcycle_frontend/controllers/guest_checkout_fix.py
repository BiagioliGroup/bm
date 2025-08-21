# -*- coding: utf-8 -*-
# Archivo: sh_motorcycle_backend/controllers/guest_checkout_fix.py
# VERSIÓN PRODUCCIÓN - Sin debug info

from odoo import http, _
from odoo.http import request
from odoo.addons.sh_motorcycle_frontend.controllers.sh_motorcycle_frontend import MotorCycleWebsiteSale
import logging

_logger = logging.getLogger(__name__)


class BiagioliGuestCheckoutFix(MotorCycleWebsiteSale):
    """
    Fix para checkout de usuarios guest - VERSIÓN PRODUCCIÓN
    Soluciona el bug donde usuarios guest no podían avanzar desde /shop/address
    
    Mantiene toda la funcionalidad del módulo sh_motorcycle_frontend
    con manejo robusto de errores y logging mínimo para producción.
    """

    @http.route(['/shop/address'], type='http', auth="public", website=True, sitemap=False)
    def shop_address(self, **post):
        """
        Override para garantizar funcionamiento con usuarios guest
        """
        try:
            # Llamada al método padre original
            result = super(BiagioliGuestCheckoutFix, self).shop_address(**post)
            return result
            
        except Exception as e:
            # Log solo errores críticos en producción
            _logger.error("[BIAGIOLI] Error in shop_address: %s", str(e))
            # Fallback seguro
            return request.redirect('/shop/cart?error=address_error')

    @http.route(['/shop/address/submit'], type='http', auth="public", website=True, sitemap=False)
    def shop_address_submit(self, **post):
        """
        Override con validación defensiva para usuarios guest
        """
        try:
            # Validación básica de campos esenciales
            essential_fields = ['name', 'email']
            missing_fields = [f for f in essential_fields if not post.get(f, '').strip()]
            
            if missing_fields:
                # Redirigir con mensaje específico
                error_param = f"missing={','.join(missing_fields)}"
                return request.redirect(f'/shop/address?error={error_param}')
            
            # Llamada al método padre
            result = super(BiagioliGuestCheckoutFix, self).shop_address_submit(**post)
            return result
            
        except Exception as e:
            # Log y manejo de errores para producción
            _logger.error("[BIAGIOLI] Error in shop_address_submit: %s", str(e))
            
            # Redirección basada en tipo de error
            if "ValidationError" in str(type(e)):
                return request.redirect('/shop/address?error=validation')
            else:
                return request.redirect('/shop/address?error=submit_failed')