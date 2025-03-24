# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.addons.payment.models.payment_provider import PROVIDER_SELECTION
import requests
import json
import logging

PROVIDER_SELECTION.append(('viumi', "VIÜMI"))

_logger = logging.getLogger(__name__)

class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    
    # Campos de configuración
    viumi_client_id = fields.Char(string="VIÜMI Client ID", help="ID público proporcionado por VIÜMI")
    viumi_client_secret = fields.Char(string="VIÜMI Client Secret", help="Clave privada proporcionada por VIÜMI")
    viumi_sandbox_mode = fields.Boolean(string="Modo Sandbox", default=True)

    def _viumi_get_api_url(self):
        """Retorna la base_url de la API según entorno"""
        return "https://sandbox.viumi.com.ar" if self.viumi_sandbox_mode else "https://api.viumi.com.ar"

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
