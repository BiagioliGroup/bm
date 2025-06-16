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
    iva = fields.Monetary(string="IVA", currency_field="moneda_id")
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
        '001': 'A', '002': 'A', '003': 'A', '004': 'A', '005': 'A',
        '006': 'B', '007': 'B', '008': 'B', '009': 'B', '010': 'B',
        '011': 'C', '012': 'C', '013': 'C', '015': 'C', '016': 'C',
        '051': 'M', '052': 'M', '053': 'M', '054': 'M', '055': 'M',
        '201': 'A', '206': 'B', '211': 'C',
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
            """
            Calcula percepciones/impuestos a partir de la diferencia entre total y neto+iva,
            solo si la moneda es ARS/PES. Agrupa por tipo permitiendo múltiples percepciones acumuladas.
            """
            if not importe_neto or moneda_str.upper() not in ["ARS", "PESOS", "PES"]:
                return 0, 0, 0, 0

            otros = round(total - importe_neto - iva, 2)
            if otros <= 0:
                return 0, 0, 0, 0

            tasas_posibles = [
                (0.01238, "perc_iibb"),
                (0.015, "perc_iibb"),
                (0.045, "perc_iibb"),
                (0.04545, "perc_iibb"),
                (0.03, "perc_iva"),
                (0.011, "perc_tem"),
                (0.13352, "imp_internos"),
                (0.18545, "imp_internos"),
                (0.24017, "imp_internos"),
                (0.2406, "imp_internos"),
                (0.17959, "imp_internos"),
                (0.14546, "imp_internos"),
                (0.32783, "mixto"),  # Al final, porque representa combinación
            ]

            iibb = percep_iva = tem = internos = 0

            for tasa, tipo in tasas_posibles:
                estimado = round(importe_neto * tasa, 2)
                if estimado <= otros + 0.01:
                    if tipo == "perc_iibb":
                        iibb += estimado
                    elif tipo == "perc_iva":
                        percep_iva += estimado
                    elif tipo == "perc_tem":
                        tem += estimado
                    elif tipo == "imp_internos":
                        internos += estimado
                    elif tipo == "mixto":
                        iibb += round(importe_neto * 0.2506921369, 2)
                        percep_iva += round(importe_neto * 0.07713842, 2)
                        estimado = round(importe_neto * 0.32783, 2)

                    otros -= estimado
                    otros = round(otros, 2)
                    if otros <= 0:
                        break

            return iibb, percep_iva, tem, internos




        tipo_map = self.TIPO_MAP
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
            letra = tipo_map.get(tipo_codigo, "X")
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

            # Calcular impuestos
            importe_neto = float(comp.get("Imp. Neto Gravado", 0))
            iva = float(comp.get("IVA", 0))
            total = float(comp.get("Imp. Total", 0))
            iibb, percep_iva, tem, internos = calcular_impuestos(importe_neto, iva, total, moneda_raw)

            comprobante_model.create({
                "company_id": self.env.company.id,
                "fecha_emision": comp["Fecha"],
                "letra": letra,
                "punto_venta": punto_venta,
                "nro_comprobante": numero,
                "tipo_comprobante": f"FA-{letra} {punto_venta}-{numero}",
                "razon_social_emisor": comp["Denominación Receptor/Emisor"],
                "cuit_emisor": cuit_arca,
                "iva": iva,
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
    
    