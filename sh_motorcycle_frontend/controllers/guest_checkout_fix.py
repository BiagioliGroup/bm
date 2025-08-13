# -*- coding: utf-8 -*-

from odoo import http, _
from odoo.http import request
from odoo.addons.sh_motorcycle_frontend.controllers.sh_motorcycle_frontend import MotorCycleWebsiteSale
import logging
import json

_logger = logging.getLogger(__name__)


class BiagioliGuestCheckoutFix(MotorCycleWebsiteSale):
    """
    Extensión específica para solucionar el bug de checkout guest
    en el módulo sh_motorcycle_frontend
    """

    @http.route(['/shop/address/submit'], type='http', methods=['POST'], auth='public', website=True, sitemap=False)
    def shop_address_submit(self, partner_id=None, address_type='billing', use_delivery_as_billing=None, 
                           callback=None, required_fields=None, **form_data):
        """
        Override del shop_address_submit para manejar mejor los usuarios guest
        Soluciona el problema específico donde usuarios guest se quedan atascados en /shop/address
        """
        _logger.info("[🔧 BIAGIOLI] Address submit - User: %s, Type: %s", 
                    request.env.user.name, address_type)
        _logger.info("[🔧 BIAGIOLI] Form data keys: %s", list(form_data.keys()))
        
        # Verificar que tenemos un carrito válido
        order_sudo = request.website.sale_get_order()
        if not order_sudo or not order_sudo.order_line:
            _logger.warning("[🔧 BIAGIOLI] No valid cart found, redirecting to shop")
            return json.dumps({'redirectUrl': '/shop'})
        
        # Preservar datos de motorcycle antes del submit
        self._preserve_motorcycle_data(form_data)
        
        try:
            # Llamar al método padre con manejo de errores mejorado
            result = super(BiagioliGuestCheckoutFix, self).shop_address_submit(
                partner_id=partner_id,
                address_type=address_type,
                use_delivery_as_billing=use_delivery_as_billing,
                callback=callback,
                required_fields=required_fields,
                **form_data
            )
            
            _logger.info("[🔧 BIAGIOLI] Address submit successful")
            return result
            
        except Exception as e:
            _logger.error("[🔧 BIAGIOLI] Error in address submit: %s", str(e), exc_info=True)
            
            # En caso de error, redirigir con mensaje
            error_url = '/shop/address?error=submit_failed'
            return json.dumps({'redirectUrl': error_url})

    @http.route(['/shop/address'], type='http', auth="public", website=True, sitemap=False)
    def shop_address(self, **post):
        """
        Override para mejorar el manejo de la página de address para usuarios guest
        """
        _logger.info("[🔧 BIAGIOLI] Address page - User: %s, Guest: %s", 
                    request.env.user.name, request.env.user._is_public())
        
        try:
            # Llamar al método padre
            result = super(BiagioliGuestCheckoutFix, self).shop_address(**post)
            
            # Agregar contexto adicional para debugging y mejoras
            if hasattr(result, 'qcontext'):
                result.qcontext.update({
                    'biagioli_guest_fix_active': True,
                    'is_guest_user': request.env.user._is_public(),
                    'motorcycle_data': self._get_motorcycle_session_data(),
                    'debug_mode': request.env['ir.config_parameter'].sudo().get_param('website_sale.checkout_debug', False)
                })
                
                # Log para debugging
                _logger.info("[🔧 BIAGIOLI] Address context updated with guest fix data")
                
            return result
            
        except Exception as e:
            _logger.error("[🔧 BIAGIOLI] Error in address page: %s", str(e), exc_info=True)
            
            # Fallback al controlador base de website_sale
            from odoo.addons.website_sale.controllers.main import WebsiteSale
            base_controller = WebsiteSale()
            return base_controller.shop_address(**post)

    def _preserve_motorcycle_data(self, form_data):
        """
        Preserva los datos de motorcycle en la sesión durante el checkout
        """
        session = request.session
        
        # Guardar datos de motorcycle si están presentes en el form
        motorcycle_fields = ['motorcycle_type', 'motorcycle_make', 'motorcycle_model', 'motorcycle_year']
        for field in motorcycle_fields:
            if form_data.get(field):
                session[f'biagioli_{field}'] = form_data[field]
                _logger.debug("[🔧 BIAGIOLI] Preserved %s: %s", field, form_data[field])

    def _get_motorcycle_session_data(self):
        """
        Recupera datos de motorcycle guardados en la sesión
        """
        session = request.session
        return {
            'motorcycle_type': session.get('biagioli_motorcycle_type', ''),
            'motorcycle_make': session.get('biagioli_motorcycle_make', ''),
            'motorcycle_model': session.get('biagioli_motorcycle_model', ''),
            'motorcycle_year': session.get('biagioli_motorcycle_year', ''),
        }

    @http.route(['/shop/checkout'], type='http', auth="public", website=True, sitemap=False)
    def shop_checkout(self, **post):
        """
        Override para asegurar que el checkout funcione correctamente después del fix de address
        """
        _logger.info("[🔧 BIAGIOLI] Checkout page - User: %s", request.env.user.name)
        
        try:
            result = super(BiagioliGuestCheckoutFix, self).shop_checkout(**post)
            
            if hasattr(result, 'qcontext'):
                # Restaurar datos de motorcycle si es necesario
                motorcycle_data = self._get_motorcycle_session_data()
                if any(motorcycle_data.values()):
                    result.qcontext.update({
                        'motorcycle_data': motorcycle_data,
                        'biagioli_checkout_enhanced': True
                    })
                    _logger.info("[🔧 BIAGIOLI] Motorcycle data restored in checkout")
                    
            return result
            
        except Exception as e:
            _logger.error("[🔧 BIAGIOLI] Error in checkout: %s", str(e), exc_info=True)
            return request.redirect('/shop/cart?error=checkout_failed')