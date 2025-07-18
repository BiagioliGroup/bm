import re
from odoo import _, models, fields, api
from odoo.tools import float_repr
from odoo.exceptions import UserError
from odoo.http import request
from odoo.tools import format_datetime
import json
import requests
import logging
import requests
from datetime import timedelta
import base64
import io
import xlsxwriter
from io import BytesIO




_logger = logging.getLogger(__name__)

class ComprobanteArca(models.Model):
    _name = 'comprobante.arca'
    _description = 'Comprobante descargado desde ARCA'

    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company, required=True)
    cuit_emisor = fields.Char(string='CUIT Emisor')
    razon_social_emisor = fields.Char(string='Razón Social Emisor')
    fecha_emision = fields.Date(string='Fecha de Emisión')
    tipo_comprobante = fields.Char(string='Tipo Comprobante')
    letra = fields.Char(string='Letra')
    punto_venta = fields.Char(string='Punto de Venta')
    nro_comprobante = fields.Char(string='Número de Comprobante')
    moneda_id = fields.Many2one('res.currency', string='Moneda', default=lambda self: self.env.company.currency_id)
    importe_neto = fields.Monetary(string="Importe Neto Gravado", currency_field="moneda_id")
    iva_total = fields.Monetary(string="IVA Total", currency_field="moneda_id")
    iva_105 = fields.Monetary(string="IVA 10,5%", currency_field="moneda_id")
    iva_21 = fields.Monetary(string="IVA 21%", currency_field="moneda_id")
    iva_27 = fields.Monetary(string="IVA 27%", currency_field="moneda_id")
    perc_iibb = fields.Monetary(string="Percepción IIBB", currency_field="moneda_id")
    perc_iva = fields.Monetary(string="Percepción IVA", currency_field="moneda_id")
    perc_tem = fields.Monetary(string="Imp. municipal (TEM)", currency_field="moneda_id")
    imp_internos = fields.Monetary(string="Impuestos Internos", currency_field="moneda_id")
    importe_total = fields.Monetary(
        string='Importe Total', 
        currency_field='moneda_id'
    )
    # Definimos los dígitos para el tipo de cambio
    DIGITS_TC = (16, 4)

    tipo_cambio = fields.Float(string="Tipo de Cambio", digits=DIGITS_TC)
    codigo_autorizacion = fields.Char(string="CAE")
    estado_coincidencia = fields.Selection([
        ('coincide', 'Coincide con Odoo'),
        ('solo_arca', 'Solo en ARCA'),
        ('solo_odoo', 'Solo en Odoo'),
    ], string='Estado de coincidencia', default='solo_arca')
    incluir_en_ddjj = fields.Boolean(string='¿Incluir en DDJJ?', default=True)
    clave_comparacion = fields.Char(string="Clave Comparación")
    clave_debug = fields.Char(string="Clave Debug", readonly=True)

    
    


    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        ctx = self.env.context

        if ctx.get('default_show_notification') and ctx.get('request'):
            mensaje = "Los comprobantes han sido importados correctamente."
            if ctx.get('default_duplicados_omitidos'):
                mensaje += f" Se omitieron {ctx['default_duplicados_omitidos']} comprobantes duplicados."

            ctx['request'].env['bus.bus']._sendone(
                self.env.user.partner_id, 'notification',
                {
                    'type': 'success',
                    'title': 'Importación exitosa',
                    'message': mensaje,
                    'sticky': False,
                }
            )
        return res
    
    



class WizardImportarComprobantes(models.TransientModel):
    _name = 'wizard.importar.comprobantes'
    _description = 'Importar Comprobantes desde ARCA'

    fecha_desde = fields.Date(string="Desde")
    fecha_hasta = fields.Date(string="Hasta")
    descarga_emitidos = fields.Boolean(string="Descargar Emitidos", default=False)
    descarga_recibidos = fields.Boolean(string="Descargar Recibidos", default=True)
    lote_id = fields.Many2one('arca.lote', string="Lote ya descargado")

    TIPO_MAP = {
                '001': {'codigo': 'FCA', 'signo': 1},
                '002': {'codigo': 'NDA', 'signo': 1},
                '003': {'codigo': 'NCA', 'signo': -1},
                '004': {'codigo': 'REC-A', 'signo': 1},
                '005': {'codigo': 'Nota Venta Contado A', 'signo': 1},
                '006': {'codigo': 'FCB', 'signo': 1},
                '007': {'codigo': 'NDB', 'signo': 1},
                '008': {'codigo': 'NCB', 'signo': -1},
                '009': {'codigo': 'REC-B', 'signo': 1},
                '010': {'codigo': 'Nota Venta Contado B', 'signo': 1},
                '011': {'codigo': 'FCC', 'signo': 1},
                '012': {'codigo': 'NDC', 'signo': 1},
                '013': {'codigo': 'NCC', 'signo': -1},
                '015': {'codigo': 'REC-C', 'signo': 1},
                '016': {'codigo': 'Nota Venta Contado C', 'signo': 1},
                '017': {'codigo': 'LSP-A', 'signo': 1},
                '018': {'codigo': 'LSP-B', 'signo': 1},
                '019': {'codigo': 'FEXP', 'signo': 1},
                '020': {'codigo': 'ND-EXT', 'signo': 1},
                '021': {'codigo': 'NC-EXT', 'signo': -1},
                '022': {'codigo': 'FEXP-SIMPLIFICADA', 'signo': 1},
                '023': {'codigo': 'COMPRA-A-PESQUERO', 'signo': 1},
                '024': {'codigo': 'CONSIG-A-PESQUERO', 'signo': 1},
                '025': {'codigo': 'COMPRA-B-PESQUERO', 'signo': 1},
                '026': {'codigo': 'CONSIG-B-PESQUERO', 'signo': 1},
                '027': {'codigo': 'LUCI-A', 'signo': 1},
                '028': {'codigo': 'LUCI-B', 'signo': 1},
                '029': {'codigo': 'LUCI-C', 'signo': 1},
                '030': {'codigo': 'COMPRA-USADOS', 'signo': 1},
                '031': {'codigo': 'MANDATO', 'signo': 1},
                '032': {'codigo': 'RECICLAJE', 'signo': 1},
                '033': {'codigo': 'LIQ-GRANOS', 'signo': 1},
                '034': {'codigo': 'COMP-A-RG1415', 'signo': 1},
                '035': {'codigo': 'COMP-B-RG1415', 'signo': 1},
                '036': {'codigo': 'COMP-C-RG1415', 'signo': 1},
                '037': {'codigo': 'ND-RG1415', 'signo': 1},
                '038': {'codigo': 'NC-RG1415', 'signo': -1},
                '039': {'codigo': 'OTROS-A-RG1415', 'signo': 1},
                '040': {'codigo': 'OTROS-B-RG1415', 'signo': 1},
                '041': {'codigo': 'OTROS-C-RG1415', 'signo': 1},
                '043': {'codigo': 'NC-LUCI-B', 'signo': -1},
                '044': {'codigo': 'NC-LUCI-C', 'signo': -1},
                '045': {'codigo': 'ND-LUCI-A', 'signo': 1},
                '046': {'codigo': 'ND-LUCI-B', 'signo': 1},
                '047': {'codigo': 'ND-LUCI-C', 'signo': 1},
                '048': {'codigo': 'NC-LUCI-A', 'signo': -1},
                '049': {'codigo': 'COMPRA-NR', 'signo': 1},
                '050': {'codigo': 'REC-FCA-FCE', 'signo': 1},
                '051': {'codigo': 'FCM', 'signo': 1},
                '052': {'codigo': 'NDM', 'signo': 1},
                '053': {'codigo': 'NCM', 'signo': -1},
                '054': {'codigo': 'REC-M', 'signo': 1},
                '055': {'codigo': 'Nota Venta Contado M', 'signo': 1},
                '056': {'codigo': 'COMP-M-RG1415', 'signo': 1},
                '057': {'codigo': 'OTROS-M-RG1415', 'signo': 1},
                '058': {'codigo': 'CVyLP-M', 'signo': 1},
                '059': {'codigo': 'LIQ-M', 'signo': 1},
                '060': {'codigo': 'CVyLP-A', 'signo': 1},
                '061': {'codigo': 'CVyLP-B', 'signo': 1},
                '063': {'codigo': 'LIQ-A', 'signo': 1},
                '064': {'codigo': 'LIQ-B', 'signo': 1},
                '066': {'codigo': 'IMP-IMPORTACION', 'signo': 1},
                '068': {'codigo': 'LIQ-C', 'signo': 1},
                '070': {'codigo': 'REC-FCE', 'signo': 1},
                '080': {'codigo': 'ZETA', 'signo': 1},
                '081': {'codigo': 'TQ-FCA', 'signo': 1},
                '082': {'codigo': 'TQ-FCB', 'signo': 1},
                '083': {'codigo': 'TIQUE', 'signo': 1},
                '088': {'codigo': 'REMITO-E', 'signo': 1},
                '089': {'codigo': 'RESUMEN', 'signo': 1},
                '090': {'codigo': 'OTROS-EXC-NC', 'signo': -1},
                '091': {'codigo': 'REMITO-R', 'signo': 1},
                '099': {'codigo': 'OTROS', 'signo': 1},
                '110': {'codigo': 'TQ-NC', 'signo': -1},
                '111': {'codigo': 'TQ-FCC', 'signo': 1},
                '112': {'codigo': 'TQ-NCA', 'signo': -1},
                '113': {'codigo': 'TQ-NCB', 'signo': -1},
                '114': {'codigo': 'TQ-NCC', 'signo': -1},
                '115': {'codigo': 'TQ-NDA', 'signo': 1},
                '116': {'codigo': 'TQ-NDB', 'signo': 1},
                '117': {'codigo': 'TQ-NDC', 'signo': 1},
                '118': {'codigo': 'TQ-FCM', 'signo': 1},
                '119': {'codigo': 'TQ-NCM', 'signo': -1},
                '120': {'codigo': 'TQ-NDM', 'signo': 1},
                '201': {'codigo': 'FCE-A', 'signo': 1},
                '202': {'codigo': 'ND-FCE-A', 'signo': 1},
                '203': {'codigo': 'NC-FCE-A', 'signo': -1},
                '206': {'codigo': 'FCE-B', 'signo': 1},
                '207': {'codigo': 'ND-FCE-B', 'signo': 1},
                '208': {'codigo': 'NC-FCE-B', 'signo': -1},
                '211': {'codigo': 'FCE-C', 'signo': 1},
                '212': {'codigo': 'ND-FCE-C', 'signo': 1},
                '213': {'codigo': 'NC-FCE-C', 'signo': -1},
                '331': {'codigo': 'LIQ-SEC-GRANOS', 'signo': 1},
                '332': {'codigo': 'CERT-E-GRANOS', 'signo': 1},
                '995': {'codigo': 'REMITO-CARNICO-E', 'signo': 1},
            }



    def _buscar_lote_existente(self):
        return self.env['arca.lote'].search([
            ('fecha_desde', '=', self.fecha_desde),
            ('fecha_hasta', '=', self.fecha_hasta),
            ('usado', '=', False),
        ], limit=1)

    def _consultar_api_arca(self):
        config = self.env['arca.settings'].search([], limit=1)
        if not config or not config.api_key:
            raise UserError("Debe configurar su API Key en el Panel Cliente ARCA.")

        payload = {
            "desde": self.fecha_desde.strftime("%d/%m/%Y"),
            "hasta": self.fecha_hasta.strftime("%d/%m/%Y"),
            "cuit_inicio_sesion": config.cuit_representante,
            "representado_nombre": config.nombre,
            "representado_cuit": config.cuit,
            "contrasena": config.clave_fiscal,
            "descarga_emitidos": self.descarga_emitidos,
            "descarga_recibidos": self.descarga_recibidos,
        }

        headers = {
            "x-api-key": config.api_key,
            "email": config.email,
        }

        url = "https://api-bot-mc.mrbot.com.ar/api/v1/comprobantes/consulta"
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            raise UserError(f"Error al consultar ARCA: {response.text}")

        data = response.json()

        if not data.get("success"):
            raise UserError(f"Consulta fallida: {data.get('message')}")

        # Descontar consulta
        if config.consultas_disponibles > 0:
            config.consultas_disponibles -= 1

        return data

    def action_importar(self):
        lote_existente = self._buscar_lote_existente()

        if lote_existente:
            data = lote_existente.cargar_dict()
        else:
            data = self._consultar_api_arca()
            lote_existente = self.env['arca.lote'].guardar_lote(
                self.env, self.fecha_desde, self.fecha_hasta, data
            )

        # Procesar el lote de comprobantes
        duplicados_omitidos = self._procesar_comprobantes(data)

        lote_existente.usado = True

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Importación completada",
                "message": (
                    f"Se importaron correctamente. Se omitieron {duplicados_omitidos} duplicados."
                    if duplicados_omitidos else
                    "Los comprobantes han sido importados correctamente."
                ),
                "type": "success",
                "sticky": False,
                "next": None
            }
        }
    

    def _procesar_comprobantes(self, data):
        import re

        def normalize_cuit(cuit):
            return cuit.replace("-", "").replace(" ", "").strip() if cuit else ""

        def build_clave(cuit, punto_vta, numero):
            return f"{normalize_cuit(cuit)}-{str(punto_vta).zfill(5)}-{str(numero).zfill(8)}"

        def calcular_impuestos(importe_neto, iva, total, moneda_str):
            if not importe_neto or moneda_str.upper() not in ["ARS", "PESOS", "PES"]:
                return 0, 0, 0, 0

            otros = round(total - importe_neto - iva, 2)
            if otros <= 0:
                return 0, 0, 0, 0

            porcentaje_otro = round(otros / importe_neto, 6)
            iibb = perc_iva = tem = internos = 0

            # Fase 1: mono-impuesto exacto
            mono_tasas = {
                0.015: "perc_iibb",
                0.025: "perc_iibb",
                0.035: "perc_iibb",
                0.055: "perc_iibb",
                0.03: "perc_iva",
                0.011: "perc_tem",
            }

            for tasa, tipo in mono_tasas.items():
                if abs(porcentaje_otro - tasa) < 0.0005:
                    estimado = round(importe_neto * tasa, 2)
                    if tipo == "perc_iibb":
                        iibb = estimado
                    elif tipo == "perc_iva":
                        perc_iva = estimado
                    elif tipo == "perc_tem":
                        tem = estimado
                    return iibb, perc_iva, tem, internos

            # Fase 2: combinaciones conocidas
            combinaciones = {
                0.045: [("perc_iibb", 0.03), ("perc_iva", 0.015)],
                0.041: [("perc_iibb", 0.03), ("perc_tem", 0.011)],
                0.056: [("perc_iibb", 0.03), ("perc_iva", 0.015), ("perc_tem", 0.011)],
                0.4892218: [("perc_iibb", 0.30707), ("perc_iva", 0.1821518)],  # MercadoLibre real
            }

            for total_tasa, partes in combinaciones.items():
                if abs(porcentaje_otro - total_tasa) < 0.0005:
                    for tipo, tasa in partes:
                        estimado = round(importe_neto * tasa, 2)
                        if tipo == "perc_iibb":
                            iibb += estimado
                        elif tipo == "perc_iva":
                            perc_iva += estimado
                        elif tipo == "perc_tem":
                            tem += estimado
                    return iibb, perc_iva, tem, internos

            # Fallback: nada detectado
            return 0, 0, 0, 0




        tipo_map = self.TIPO_MAP
        # Si el usuario no completó fechas, las tomamos del lote seleccionado
        if not self.fecha_desde and self.lote_id:
            self.fecha_desde = self.lote_id.fecha_desde
        if not self.fecha_hasta and self.lote_id:
            self.fecha_hasta = self.lote_id.fecha_hasta
            
        comprobante_model = self.env['comprobante.arca']
        move_model = self.env['account.move']

        existentes = set(
            comprobante_model.search([]).mapped(
                lambda r: f"{normalize_cuit(r.cuit_emisor)}-{r.punto_venta}-{r.nro_comprobante}"
            )
        )

        claves_odoo = {
            build_clave(m.partner_id.vat, *re.search(r'(\d{5})[- ]?(\d{8})', m.name or "").groups()): m.id
            for m in move_model.search([
                ('move_type', 'in', ['in_invoice', 'in_refund']),
                ('name', '!=', False),
                ('partner_id.vat', '!=', False)
            ])
            if re.search(r'\d{5}[- ]?\d{8}', m.name or "")
        }

        duplicados = 0
        for comp in data.get("mis_comprobantes_recibidos", []):
            tipo_codigo = str(comp["Tipo"]).zfill(3)
            tipo_info = self.TIPO_MAP.get(tipo_codigo, {'codigo': '??', 'signo': 1})

            letra = tipo_info['codigo']
            signo = tipo_info['signo']
            punto_venta = str(comp["Punto de Venta"]).zfill(5)
            numero = str(comp["Número Desde"]).zfill(8)
            cuit_arca = comp['Nro. Doc. Receptor/Emisor']
            clave = build_clave(cuit_arca, punto_venta, numero)

            if clave in existentes:
                duplicados += 1
                continue

            existentes.add(clave)
            estado = 'coincide' if clave in claves_odoo else 'solo_arca'
            clave_debug = f"{{{clave}}} & {{{clave if clave in claves_odoo else 'NO_MATCH'}}}"
            moneda_raw = comp.get("Moneda", "PES")
            moneda = self.env['res.currency'].search([('name', 'ilike', moneda_raw)], limit=1)

            # Calcular impuestos y valores monetarios
            importe_neto = signo * float(comp.get("Imp. Neto Gravado", 0))
            iva_total = signo * float(comp.get("IVA", 0))
            iva_105 =  iva_21 = iva_27 = 0.0
            # Intentamos calcular distribución de IVA
            if iva_total:
                porc = round(iva_total / importe_neto, 4)  # ratio total IVA sobre neto
                if abs(porc - 0.105) < 0.001:
                    iva_105 = iva_total
                elif abs(porc - 0.21) < 0.001:
                    iva_21 = iva_total
                elif abs(porc - 0.27) < 0.001:
                    iva_27 = iva_total
                else:
                    # Descomposición múltiple si aplica
                    # En este punto podrías añadir lógica futura como hiciste con percepciones
                    iva_21 = iva_total  # fallback: todo a 21%
            total = signo * float(comp.get("Imp. Total", 0))
            iibb, percep_iva, tem, internos = calcular_impuestos(signo * importe_neto, signo * iva_total, signo * total, signo * moneda_raw)
            

            comprobante_model.create({
                "company_id": self.env.company.id,
                "fecha_emision": comp["Fecha"],
                "letra": letra,
                "punto_venta": punto_venta,
                "nro_comprobante": numero,
                "tipo_comprobante": f"{letra} {punto_venta}-{numero}",
                "razon_social_emisor": comp["Denominación Receptor/Emisor"],
                "cuit_emisor": cuit_arca,
                "iva_total": iva_total,
                "iva_105": iva_105,
                "iva_21": iva_21,
                "iva_27": iva_27,
                "importe_total": total,
                "importe_neto": importe_neto,
                "tipo_cambio": float(comp.get("Tipo Cambio", 1.0)),
                "codigo_autorizacion": comp.get("Cód. Autorización"),
                "moneda_id": moneda.id,
                "estado_coincidencia": estado,
                "clave_comparacion": clave,
                "clave_debug": clave_debug,
                "perc_iibb": iibb,
                "perc_iva": percep_iva,
                "perc_tem": tem,
                "imp_internos": internos,
            })
            
        # Paso final: buscar comprobantes que solo están en Odoo en el rango de fechas
        
        fecha_desde = self.fecha_desde
        fecha_hasta = self.fecha_hasta
        moves_odoo = move_model.search([
            ('move_type', 'in', ['in_invoice', 'in_refund']),
            ('invoice_date', '>=', fecha_desde),
            ('invoice_date', '<=', fecha_hasta),
            ('name', '!=', False),
            ('partner_id.vat', '!=', False),
        ])

        for move in moves_odoo:
            match = re.search(r'(\d{5})[- ]?(\d{8})', move.name or "")
            if not match:
                continue

            punto_venta, numero = match.groups()
            clave = build_clave(move.partner_id.vat, punto_venta, numero)

            if clave in existentes:
                continue  # Ya fue creado con estado 'coincide' o 'solo_arca'

            existentes.add(clave)
            moneda = move.currency_id
 
            # Aqui adaptamos el tipo de comprobante desde ODOO
            match = re.search(r'([A-Z]{2})-([A-Z]) (\d{5})-(\d{8})', move.name or '')
            if match:
                tipo = match.group(1)         # FA
                letra = match.group(2)        # A
                punto_venta = match.group(3)  # 00010
                numero = match.group(4)       # 00000038
            else:
                tipo = move.name or ""
                letra = ""
                punto_venta = ""
                numero = ""

            TIPO_MAP = {
            "FA-A": "FCA", "ND-A": "NDA", "NC-A": "NCA",
            "FA-B": "FCB", "ND-B": "NDB", "NC-B": "NCB",
            "FA-C": "FCC", "ND-C": "NDC", "NC-C": "NCC",
            "FA-M": "FCM", "ND-M": "NDM", "NC-M": "NCM",
            # Agregá más según necesites
        }

            def get_tipo_comprobante_code(move_name):
                match = re.match(r"([A-Z]{2})-([A-Z])\s+\d{5}-\d+", move_name)
                if match:
                    tipo = match.group(1)  # ej: FA
                    letra = match.group(2)  # ej: A
                    return TIPO_MAP.get(f"{tipo}-{letra}", "DESCONOCIDO")
                return "DESCONOCIDO"
            
            comprobante_model.create({
                "company_id": move.company_id.id,
                "fecha_emision": move.invoice_date,
                "letra": get_tipo_comprobante_code(move.name),  
                "punto_venta": punto_venta,
                "nro_comprobante": numero,
                "tipo_comprobante": move.name,
                "razon_social_emisor": move.partner_id.name,
                "cuit_emisor": move.partner_id.vat,
                "iva_total": move.amount_tax,
                "importe_total": move.amount_total,
                "importe_neto": move.amount_untaxed,
                "tipo_cambio": float(comp.get("Tipo Cambio", 1.0)),
                "codigo_autorizacion": "",  # No disponible
                "moneda_id": moneda.id,
                "estado_coincidencia": "solo_odoo",
                "clave_comparacion": clave,
                "clave_debug": f"{{NO_ARCA}} & {{{clave}}}",
            })


        return duplicados



    
    def action_procesar_lote(self):
        self.ensure_one()

        if not self.lote_id:
            raise UserError("Debe seleccionar un lote previamente descargado.")

        data = self.lote_id.cargar_dict()
        duplicados_omitidos = self._procesar_comprobantes(data)
        self.lote_id.usado = True

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Lote procesado",
                "message": (
                    f"Se procesó el lote seleccionado. Se omitieron {duplicados_omitidos} duplicados."
                    if duplicados_omitidos else
                    "Lote procesado correctamente sin duplicados."
                ),
                "type": "success",
                "sticky": False,
                "next": {
                    "type": "ir.actions.act_window",
                    "res_model": "comprobante.arca",
                    "view_mode": "list,form",
                    "target": "current",
                }
            }
        }


    


class ArcaLote(models.Model):
    _name = 'arca.lote'
    _description = 'Lote de Comprobantes ARCA'

    name = fields.Char(string='Nombre', required=True, default=lambda self: _('Nuevo'))
    fecha_desde = fields.Date(string="Desde")
    fecha_hasta = fields.Date(string="Hasta")
    datos_json = fields.Text(string="JSON crudo ARCA")
    usado = fields.Boolean(string="Ya fue procesado", default=False)
    

    @api.model
    def create(self, vals):
        if vals.get('fecha_desde') and vals.get('fecha_hasta') and not vals.get('name'):
            vals['name'] = f"Lote {vals['fecha_desde']} - {vals['fecha_hasta']}"
        return super().create(vals)

    @classmethod
    def guardar_lote(cls, env, fecha_desde, fecha_hasta, datos_dict):
        return env['arca.lote'].create({
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
            'datos_json': json.dumps(datos_dict, indent=2, ensure_ascii=False),
        })

    def cargar_dict(self):
        return json.loads(self.datos_json or "{}")
    
    