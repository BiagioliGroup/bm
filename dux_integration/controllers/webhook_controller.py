# -*- coding: utf-8 -*-
import json
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class DuxWebhookController(http.Controller):
    
    @http.route('/dux/webhook', type='json', auth='none', methods=['POST'], csrf=False)
    def dux_webhook(self, **kwargs):
        """Endpoint para recibir webhooks de Dux Software"""
        try:
            # Obtener datos del webhook
            data = request.jsonrequest
            _logger.info(f"Webhook recibido de Dux: {data}")
            
            # Validar estructura básica
            if not data or 'event' not in data:
                return {'status': 'error', 'message': 'Estructura de webhook inválida'}
            
            event_type = data.get('event')
            event_data = data.get('data', {})
            
            # Procesar según tipo de evento
            if event_type == 'cliente.created':
                return self._handle_cliente_created(event_data)
            elif event_type == 'cliente.updated':
                return self._handle_cliente_updated(event_data)
            elif event_type == 'producto.created':
                return self._handle_producto_created(event_data)
            elif event_type == 'producto.updated':
                return self._handle_producto_updated(event_data)
            elif event_type == 'venta.created':
                return self._handle_venta_created(event_data)
            elif event_type == 'stock.updated':
                return self._handle_stock_updated(event_data)
            else:
                _logger.warning(f"Tipo de evento no manejado: {event_type}")
                return {'status': 'ignored', 'message': f'Evento {event_type} ignorado'}
            
        except Exception as e:
            _logger.error(f"Error procesando webhook Dux: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def _handle_cliente_created(self, data):
        """Maneja creación de cliente"""
        try:
            mapper = request.env['dux.data.mapper'].sudo()
            partner_data = mapper.map_cliente_to_partner(data)
            
            # Verificar si ya existe
            existing = request.env['res.partner'].sudo().search([
                ('vat', '=', data.get('cuit'))
            ], limit=1)
            
            if not existing:
                partner = request.env['res.partner'].sudo().create(partner_data)
                _logger.info(f"Cliente creado vía webhook: {partner.name}")
                return {'status': 'success', 'partner_id': partner.id}
            else:
                return {'status': 'exists', 'partner_id': existing.id}
                
        except Exception as e:
            _logger.error(f"Error creando cliente vía webhook: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def _handle_cliente_updated(self, data):
        """Maneja actualización de cliente"""
        try:
            # Buscar cliente existente
            partner = request.env['res.partner'].sudo().search([
                ('vat', '=', data.get('cuit'))
            ], limit=1)
            
            if partner:
                mapper = request.env['dux.data.mapper'].sudo()
                partner_data = mapper.map_cliente_to_partner(data)
                partner.write(partner_data)
                _logger.info(f"Cliente actualizado vía webhook: {partner.name}")
                return {'status': 'updated', 'partner_id': partner.id}
            else:
                return {'status': 'not_found', 'message': 'Cliente no encontrado'}
                
        except Exception as e:
            _logger.error(f"Error actualizando cliente vía webhook: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def _handle_producto_created(self, data):
        """Maneja creación de producto"""
        try:
            mapper = request.env['dux.data.mapper'].sudo()
            product_data = mapper.map_producto_to_product(data)
            
            # Verificar si ya existe
            existing = request.env['product.product'].sudo().search([
                ('default_code', '=', data.get('codigo'))
            ], limit=1)
            
            if not existing:
                product = request.env['product.product'].sudo().create(product_data)
                _logger.info(f"Producto creado vía webhook: {product.name}")
                return {'status': 'success', 'product_id': product.id}
            else:
                return {'status': 'exists', 'product_id': existing.id}
                
        except Exception as e:
            _logger.error(f"Error creando producto vía webhook: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def _handle_producto_updated(self, data):
        """Maneja actualización de producto"""
        try:
            # Buscar producto existente
            product = request.env['product.product'].sudo().search([
                ('default_code', '=', data.get('codigo'))
            ], limit=1)
            
            if product:
                mapper = request.env['dux.data.mapper'].sudo()
                product_data = mapper.map_producto_to_product(data)
                product.write(product_data)
                _logger.info(f"Producto actualizado vía webhook: {product.name}")
                return {'status': 'updated', 'product_id': product.id}
            else:
                return {'status': 'not_found', 'message': 'Producto no encontrado'}
                
        except Exception as e:
            _logger.error(f"Error actualizando producto vía webhook: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def _handle_venta_created(self, data):
        """Maneja creación de venta"""
        try:
            mapper = request.env['dux.data.mapper'].sudo()
            sale_data = mapper.map_venta_to_sale_order(data)
            
            # Verificar si ya existe
            existing = request.env['sale.order'].sudo().search([
                ('client_order_ref', '=', data.get('numero'))
            ], limit=1)
            
            if not existing:
                sale_order = request.env['sale.order'].sudo().create(sale_data)
                _logger.info(f"Venta creada vía webhook: {sale_order.name}")
                return {'status': 'success', 'sale_id': sale_order.id}
            else:
                return {'status': 'exists', 'sale_id': existing.id}
                
        except Exception as e:
            _logger.error(f"Error creando venta vía webhook: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def _handle_stock_updated(self, data):
        """Maneja actualización de stock"""
        try:
            product = request.env['product.product'].sudo().search([
                ('default_code', '=', data.get('codigo_producto'))
            ], limit=1)
            
            if product:
                new_qty = float(data.get('cantidad', 0))
                
                # Buscar quant existente
                quant = request.env['stock.quant'].sudo().search([
                    ('product_id', '=', product.id),
                    ('location_id.usage', '=', 'internal')
                ], limit=1)
                
                if quant:
                    quant.quantity = new_qty
                else:
                    request.env['stock.quant'].sudo().create({
                        'product_id': product.id,
                        'location_id': request.env.ref('stock.stock_location_stock').id,
                        'quantity': new_qty,
                    })
                
                _logger.info(f"Stock actualizado vía webhook: {product.name} = {new_qty}")
                return {'status': 'updated', 'product_id': product.id, 'quantity': new_qty}
            else:
                return {'status': 'not_found', 'message': 'Producto no encontrado'}
                
        except Exception as e:
            _logger.error(f"Error actualizando stock vía webhook: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    @http.route('/dux/webhook/test', type='http', auth='none', methods=['GET'])
    def webhook_test(self):
        """Endpoint de prueba para webhooks"""
        return "Webhook Dux funcionando correctamente"