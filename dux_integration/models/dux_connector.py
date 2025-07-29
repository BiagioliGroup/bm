# -*- coding: utf-8 -*-
import requests
import json
import logging
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class DuxConnector(models.Model):
    _name = 'dux.connector'
    _description = 'Conector API Dux Software'
    _rec_name = 'name'

    name = fields.Char('Nombre', required=True, default='Conexión Dux')
    base_url = fields.Char('URL Base API', required=True, 
                          default='https://erp.duxsoftware.com.ar',
                          help='URL base de la API de Dux Software')
    api_key = fields.Char('API Key', required=True,
                         help='Clave de API proporcionada por Dux')
    id_empresa = fields.Char('ID Empresa', required=True,
                            help='ID de empresa en Dux Software')
    company_id = fields.Many2one('res.company', 'Empresa', 
                               default=lambda self: self.env.company)
    active = fields.Boolean('Activo', default=True)
    last_sync = fields.Datetime('Última Sincronización')
    
    # Status fields
    connection_status = fields.Selection([
        ('disconnected', 'Desconectado'),
        ('connected', 'Conectado'),
        ('error', 'Error')
    ], string='Estado Conexión', default='disconnected')
    
    @api.model
    def _get_headers(self):
        """Obtiene headers para requests a la API de Dux"""
        return {
            'accept': 'application/json',
            'authorization': self.api_key,  # Sin "Bearer", solo el token directo
            'Content-Type': 'application/json'
        }
    
    def test_connection(self):
        """Prueba la conexión con la API de Dux"""
        try:
            # Probar con un endpoint simple de empresas
            url = f"{self.base_url}/WSERP/rest/services/empresas"
            params = {'idEmpresa': self.id_empresa}
            response = requests.get(url, headers=self._get_headers(), params=params, timeout=30)
            
            if response.status_code == 200:
                self.connection_status = 'connected'
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Conexión Exitosa'),
                        'message': _('La conexión con Dux Software fue exitosa'),
                        'type': 'success',
                    }
                }
            else:
                self.connection_status = 'error'
                raise UserError(f"Error de conexión: {response.status_code} - {response.text}")
                
        except requests.exceptions.RequestException as e:
            self.connection_status = 'error'
            _logger.error(f"Error al conectar con Dux API: {str(e)}")
            raise UserError(f"Error de conexión: {str(e)}")
    
    def _make_request(self, endpoint, method='GET', data=None, params=None):
        """Realiza request a la API de Dux con manejo de errores"""
        try:
            url = f"{self.base_url}{endpoint}"
            headers = self._get_headers()
            
            # Agregar idEmpresa a todos los params
            if params is None:
                params = {}
            params['idEmpresa'] = self.id_empresa
            
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data, params=params, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=data, params=params, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, params=params, timeout=30)
            
            response.raise_for_status()
            return response.json() if response.content else {}
        
        except requests.exceptions.HTTPError as e:
            _logger.error(f"HTTP Error en {endpoint}: {e}")
            raise UserError(f"Error HTTP {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            _logger.error(f"Request Error en {endpoint}: {e}")
            raise UserError(f"Error de conexión: {str(e)}")
        except json.JSONDecodeError as e:
            _logger.error(f"JSON Decode Error en {endpoint}: {e}")
            raise UserError("Error al decodificar respuesta JSON")
    
    # Métodos específicos para obtener datos de Dux
    
    def get_clientes(self, limit=100, offset=0):
        """Obtiene clientes desde Dux"""
        # Nota: No hay endpoint específico de clientes, usar empresas
        params = {'limit': limit, 'offset': offset}
        return self._make_request('/WSERP/rest/services/empresas', params=params)
    
    def get_productos(self, limit=100, offset=0):
        """Obtiene productos desde Dux"""
        params = {'limit': limit, 'offset': offset}
        return self._make_request('/WSERP/rest/services/items', params=params)
    
    def get_ventas(self, fecha_desde=None, fecha_hasta=None, limit=100, offset=0):
        """Obtiene ventas desde Dux"""
        params = {'limit': limit, 'offset': offset}
        if fecha_desde:
            params['fechaDesde'] = fecha_desde
        if fecha_hasta:
            params['fechaHasta'] = fecha_hasta
        return self._make_request('/WSERP/rest/services/facturas', params=params)
    
    def get_compras(self, fecha_desde=None, fecha_hasta=None, limit=100, offset=0):
        """Obtiene compras desde Dux"""
        params = {'limit': limit, 'offset': offset}
        if fecha_desde:
            params['fechaDesde'] = fecha_desde
        if fecha_hasta:
            params['fechaHasta'] = fecha_hasta
        return self._make_request('/WSERP/rest/services/compras', params=params)
    
    def get_stock(self, limit=100, offset=0):
        """Obtiene stock desde Dux"""
        params = {'limit': limit, 'offset': offset}
        return self._make_request('/WSERP/rest/services/deposito', params=params)
    
    def get_sucursales(self, limit=100, offset=0):
        """Obtiene sucursales desde Dux"""
        params = {'limit': limit, 'offset': offset}
        return self._make_request('/WSERP/rest/services/sucursales', params=params)
    
    def get_localidades(self, limit=100, offset=0):
        """Obtiene localidades desde Dux"""
        params = {'limit': limit, 'offset': offset}
        return self._make_request('/WSERP/rest/services/localidades', params=params)
    
    def get_lista_precios(self, limit=100, offset=0):
        """Obtiene listas de precios desde Dux"""
        params = {'limit': limit, 'offset': offset}
        return self._make_request('/WSERP/rest/services/listaprecioventa', params=params)
    
    @api.model
    def get_default_connector(self):
        """Obtiene el conector por defecto"""
        connector = self.search([('active', '=', True)], limit=1)
        if not connector:
            raise UserError(_('No hay conexiones activas configuradas con Dux Software'))
        return connector
    
    