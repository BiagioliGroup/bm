# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class DuxDataMapper(models.Model):
    _name = 'dux.data.mapper'
    _description = 'Mapeador de datos Dux a Odoo'

    @api.model
    def map_cliente_to_partner(self, dux_cliente):
        """Mapea cliente de Dux a res.partner de Odoo"""
        try:
            # Mapeo base
            partner_data = {
                'name': dux_cliente.get('razon_social') or dux_cliente.get('nombre', ''),
                'vat': dux_cliente.get('cuit'),
                'email': dux_cliente.get('email'),
                'phone': dux_cliente.get('telefono'),
                'mobile': dux_cliente.get('celular'),
                'street': dux_cliente.get('direccion'),
                'city': dux_cliente.get('ciudad'),
                'zip': dux_cliente.get('codigo_postal'),
                'is_company': bool(dux_cliente.get('razon_social')),
                'customer_rank': 1,
                'supplier_rank': 0,
                'comment': f"Importado desde Dux - ID: {dux_cliente.get('id')}",
            }
            
            # Mapeo de estado/provincia
            if dux_cliente.get('provincia'):
                state = self.env['res.country.state'].search([
                    ('name', 'ilike', dux_cliente['provincia']),
                    ('country_id', '=', self.env.ref('base.ar').id)
                ], limit=1)
                if state:
                    partner_data['state_id'] = state.id
            
            # Mapeo de país (por defecto Argentina)
            partner_data['country_id'] = self.env.ref('base.ar').id
            
            # Limpieza de datos
            partner_data = self._clean_partner_data(partner_data)
            
            return partner_data
            
        except Exception as e:
            _logger.error(f"Error mapeando cliente {dux_cliente.get('id')}: {str(e)}")
            raise UserError(f"Error en mapeo de cliente: {str(e)}")
    
    @api.model
    def map_producto_to_product(self, dux_producto):
        """Mapea producto de Dux a product.product de Odoo"""
        try:
            product_data = {
                'name': dux_producto.get('descripcion', ''),
                'default_code': dux_producto.get('codigo'),
                'barcode': dux_producto.get('codigo_barras'),
                'list_price': float(dux_producto.get('precio_venta', 0)),
                'standard_price': float(dux_producto.get('precio_costo', 0)),
                'type': 'product',  # Asumimos productos almacenables
                'sale_ok': True,
                'purchase_ok': True,
                'detailed_type': 'product',
                'description': dux_producto.get('observaciones'),
                'weight': float(dux_producto.get('peso', 0)),
            }
            
            # Mapeo de categoría
            if dux_producto.get('categoria'):
                category = self._get_or_create_category(dux_producto['categoria'])
                product_data['categ_id'] = category.id
            
            # Mapeo de unidad de medida
            if dux_producto.get('unidad_medida'):
                uom = self._get_or_create_uom(dux_producto['unidad_medida'])
                product_data['uom_id'] = uom.id
                product_data['uom_po_id'] = uom.id
            
            # Stock inicial
            if dux_producto.get('stock_actual'):
                product_data['qty_available'] = float(dux_producto['stock_actual'])
            
            product_data = self._clean_product_data(product_data)
            
            return product_data
            
        except Exception as e:
            _logger.error(f"Error mapeando producto {dux_producto.get('id')}: {str(e)}")
            raise UserError(f"Error en mapeo de producto: {str(e)}")
    
    @api.model
    def map_venta_to_sale_order(self, dux_venta):
        """Mapea venta de Dux a sale.order de Odoo"""
        try:
            # Buscar el cliente
            partner = self._find_partner_by_dux_id(dux_venta.get('cliente_id'))
            if not partner:
                raise UserError(f"Cliente no encontrado para venta {dux_venta.get('numero')}")
            
            sale_data = {
                'partner_id': partner.id,
                'date_order': self._parse_date(dux_venta.get('fecha')),
                'client_order_ref': dux_venta.get('numero'),
                'note': f"Importado desde Dux - ID: {dux_venta.get('id')}",
                'state': self._map_sale_state(dux_venta.get('estado')),
            }
            
            # Mapear líneas de venta
            order_lines = []
            for linea in dux_venta.get('lineas', []):
                line_data = self.map_venta_line_to_sale_line(linea)
                order_lines.append((0, 0, line_data))
            
            sale_data['order_line'] = order_lines
            
            return sale_data
            
        except Exception as e:
            _logger.error(f"Error mapeando venta {dux_venta.get('id')}: {str(e)}")
            raise UserError(f"Error en mapeo de venta: {str(e)}")
    
    @api.model
    def map_venta_line_to_sale_line(self, dux_linea):
        """Mapea línea de venta de Dux a sale.order.line"""
        try:
            product = self._find_product_by_dux_id(dux_linea.get('producto_id'))
            if not product:
                raise UserError(f"Producto no encontrado para línea {dux_linea.get('id')}")
            
            line_data = {
                'product_id': product.id,
                'name': product.name,
                'product_uom_qty': float(dux_linea.get('cantidad', 1)),
                'price_unit': float(dux_linea.get('precio_unitario', 0)),
                'discount': float(dux_linea.get('descuento', 0)),
            }
            
            return line_data
            
        except Exception as e:
            _logger.error(f"Error mapeando línea de venta: {str(e)}")
            raise UserError(f"Error en mapeo de línea: {str(e)}")
    
    # Métodos auxiliares
    
    def _clean_partner_data(self, data):
        """Limpia datos de partner"""
        # Remover valores None o vacíos
        cleaned = {k: v for k, v in data.items() if v not in [None, '', False]}
        
        # Validar email
        if 'email' in cleaned and cleaned['email']:
            if '@' not in cleaned['email']:
                del cleaned['email']
        
        # Validar teléfono
        if 'phone' in cleaned and cleaned['phone']:
            cleaned['phone'] = str(cleaned['phone']).strip()
        
        return cleaned
    
    def _clean_product_data(self, data):
        """Limpia datos de producto"""
        cleaned = {k: v for k, v in data.items() if v not in [None, '', False]}
        
        # Asegurar precios no negativos
        if 'list_price' in cleaned and cleaned['list_price'] < 0:
            cleaned['list_price'] = 0
        if 'standard_price' in cleaned and cleaned['standard_price'] < 0:
            cleaned['standard_price'] = 0
            
        return cleaned
    
    def _get_or_create_category(self, categoria_nombre):
        """Obtiene o crea categoría de producto"""
        category = self.env['product.category'].search([
            ('name', '=', categoria_nombre)
        ], limit=1)
        
        if not category:
            category = self.env['product.category'].create({
                'name': categoria_nombre
            })
        
        return category
    
    def _get_or_create_uom(self, uom_nombre):
        """Obtiene o crea unidad de medida"""
        uom = self.env['uom.uom'].search([
            ('name', 'ilike', uom_nombre)
        ], limit=1)
        
        if not uom:
            # Usar unidad por defecto
            uom = self.env.ref('uom.product_uom_unit')
        
        return uom
    
    def _find_partner_by_dux_id(self, dux_id):
        """Busca partner por ID de Dux en comentarios"""
        return self.env['res.partner'].search([
            ('comment', 'ilike', f'Dux - ID: {dux_id}')
        ], limit=1)
    
    def _find_product_by_dux_id(self, dux_id):
        """Busca producto por ID de Dux"""
        # Buscar por código interno o en descripción
        product = self.env['product.product'].search([
            '|',
            ('default_code', '=', str(dux_id)),
            ('name', 'ilike', f'Dux ID: {dux_id}')
        ], limit=1)
        return product
    
    def _parse_date(self, date_str):
        """Convierte string de fecha a datetime"""
        if not date_str:
            return fields.Datetime.now()
        
        try:
            # Probar diferentes formatos
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y']:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            # Si no funciona ningún formato, usar fecha actual
            return fields.Datetime.now()
            
        except Exception:
            return fields.Datetime.now()
    
    def _map_sale_state(self, dux_estado):
        """Mapea estados de venta de Dux a Odoo"""
        estado_map = {
            'borrador': 'draft',
            'confirmado': 'sale',
            'entregado': 'done',
            'cancelado': 'cancel',
        }
        return estado_map.get(dux_estado, 'draft')