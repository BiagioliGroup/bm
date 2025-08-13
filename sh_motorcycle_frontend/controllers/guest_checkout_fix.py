# -*- coding: utf-8 -*-
# Archivo: sh_motorcycle_backend/controllers/guest_checkout_fix.py

from odoo import http, _
from odoo.http import request
from odoo.addons.sh_motorcycle_frontend.controllers.sh_motorcycle_frontend import MotorCycleWebsiteSale
import logging
import json

_logger = logging.getLogger(__name__)


class BiagioliGuestCheckoutFix(MotorCycleWebsiteSale):
    """
    Parche para solucionar el bug de checkout de usuarios guest.
    Extiende MotorCycleWebsiteSale manteniendo toda la funcionalidad existente.
    """

    @http.route(['/shop/address'], type='http', auth="public", website=True, sitemap=False)
    def shop_address(self, **post):
        """
        Override mínimo para arreglar el problema con usuarios guest
        """
        user_name = request.env.user.name
        is_guest = request.env.user._is_public()
        
        _logger.info("[🔧 BIAGIOLI] shop_address - User: %s, Guest: %s", user_name, is_guest)
        
        try:
            # Llamada al método padre original
            result = super(BiagioliGuestCheckoutFix, self).shop_address(**post)
            
            # SIEMPRE agregar debug info para usuarios guest (para testing)
            if hasattr(result, 'qcontext') and is_guest:
                result.qcontext.update({
                    'biagioli_guest_debug': True,  # Siempre True para guest users
                    'user_is_guest': True,
                })
                _logger.info("[🔧 BIAGIOLI] Guest debug context added - Order: %s", 
                           result.qcontext.get('order', {}).get('id', 'No Order'))
                
            return result
            
        except Exception as e:
            _logger.error("[🔧 BIAGIOLI] Error in shop_address: %s", str(e), exc_info=True)
            # En caso de error crítico, redirigir al carrito
            return request.redirect('/shop/cart?error=address_failed')

    @http.route(['/shop/address/submit'], type='http', auth="public", website=True, sitemap=False)
    def shop_address_submit(self, **post):
        """
        Override con validación mejorada para usuarios guest
        """
        user_name = request.env.user.name
        _logger.info("[🔧 BIAGIOLI] shop_address_submit - User: %s", user_name)
        
        # Log de los campos recibidos (sin datos sensibles)
        received_fields = [k for k in post.keys() if k not in ['password', 'confirm_password']]
        _logger.debug("[🔧 BIAGIOLI] Received fields: %s", received_fields)
        
        try:
            # Validación básica defensiva
            essential_fields = ['name', 'email']
            missing_essential = [f for f in essential_fields if not post.get(f, '').strip()]
            
            if missing_essential:
                _logger.warning("[🔧 BIAGIOLI] Missing essential fields: %s", missing_essential)
                error_param = f"missing={','.join(missing_essential)}"
                return request.redirect(f'/shop/address?error={error_param}')
            
            # Llamada al método padre original
            result = super(BiagioliGuestCheckoutFix, self).shop_address_submit(**post)
            _logger.info("[🔧 BIAGIOLI] shop_address_submit completed successfully")
            return result
            
        except Exception as e:
            _logger.error("[🔧 BIAGIOLI] Error in shop_address_submit: %s", str(e), exc_info=True)
            
            # Manejo de diferentes tipos de errores
            if "ValidationError" in str(type(e)):
                return request.redirect('/shop/address?error=validation')
            elif "AccessError" in str(type(e)):
                return request.redirect('/shop/address?error=access')
            else:
                return request.redirect('/shop/address?error=unknown')