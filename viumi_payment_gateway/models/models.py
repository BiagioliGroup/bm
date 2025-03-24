# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import requests
import json
import logging
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)

class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('viumi', "VIÜMI")],
        ondelete={'viumi': 'set default'}
    )
    
    # Campos de configuración
    viumi_client_id = fields.Char(string="VIÜMI Client ID", help="ID público proporcionado por VIÜMI")
    viumi_client_secret = fields.Char(string="VIÜMI Client Secret", help="Clave privada proporcionada por VIÜMI")
    viumi_sandbox_mode = fields.Boolean(string="Modo Sandbox", default=True)

    def _viumi_get_api_url(self):
        """Base API endpoint para VIÜMI"""
        return "https://sandbox.viumi.com.ar" if self.viumi_sandbox_mode else "https://api.viumi.com.ar"

    def _viumi_get_auth_url(self):
        """Base AUTH endpoint para VIÜMI (GeoPagos Auth Server)"""
        return "https://auth.sandbox.geopagos.com" if self.viumi_sandbox_mode else "https://auth.geopagos.com"

    def _viumi_get_access_token(self):
        """Autenticación y obtención del JWT para usar en la API"""
        url = f"{self._viumi_get_api_url()}/oauth/token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.viumi_client_id,
            "client_secret": self.viumi_client_secret,
            "scope": "*"
        }
        headers = {
            "Content-Type": "application/json"
        }

        _logger.info(f"[VIUMI] Solicitando token a {url}...")

        try:
            response = requests.post(url, data=json.dumps(payload), headers=headers)
            response.raise_for_status()
            token_data = response.json()
            access_token = token_data.get("access_token")
            _logger.info("[VIUMI] Token obtenido correctamente.")
            return access_token
        except requests.exceptions.RequestException as e:
            _logger.error(f"[VIUMI] Error al obtener token: {e}")
            return None
        
    def viumi_generate_checkout_link(self, amount, concept, success_url, error_url):
        """Genera un link de pago con VIÜMI."""
        self.ensure_one()  # Por si se llama sobre un conjunto de registros

        token = self._viumi_get_access_token()
        if not token:
            raise ValueError("No se pudo obtener el token de acceso de VIÜMI")

        url = f"{self._viumi_get_api_url()}/api/public/v1/checkout"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }

        payload = {
            "concept": concept,
            "amount": float(amount),  # Monto en pesos argentinos
            "success_url": success_url,
            "error_url": error_url,
            "external_reference": self.env.company.name,  # opcional
        }

        _logger.info(f"[VIUMI] Enviando solicitud de pago: {payload}")

        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            data = response.json()
            payment_link = data.get("init_point")  # o 'url' según la respuesta
            _logger.info(f"[VIUMI] Link de pago generado: {payment_link}")
            return payment_link
        except requests.exceptions.RequestException as e:
            _logger.error(f"[VIUMI] Error al generar link de pago: {e}")
            return None
    
    def action_test_viumi_checkout(self):
        self.ensure_one()
        try:
            link = self.viumi_generate_checkout_link(
                amount=1500.00,
                concept="Prueba desde botón",
                success_url="https://biagioligroup.com.ar/pago-exitoso",
                error_url="https://biagioligroup.com.ar/pago-error"
            )
            if not link:
                raise UserError("No se generó el link de pago.")

            # Mostramos el link como popup
            return {
                'type': 'ir.actions.act_window',
                'name': 'Link de pago VIÜMI',
                'res_model': 'ir.ui.view',
                'view_mode': 'form',
                'target': 'new',
                'views': [(False, 'form')],
                'context': {
                    'default_name': 'Link de pago generado',
                    'default_arch': f'''
                        <form string="Link de Pago VIÜMI">
                            <sheet>
                                <group>
                                    <label string="Copia y pegá este link en el navegador:"/>
                                    <field name="type" invisible="1"/>
                                    <field name="arch" invisible="1"/>
                                    <div>
                                        <p><a href="{link}" target="_blank">{link}</a></p>
                                    </div>
                                </group>
                            </sheet>
                        </form>
                    ''',
                },
            }
        except Exception as e:
            raise UserError(f"Error al generar link de pago: {e}")
