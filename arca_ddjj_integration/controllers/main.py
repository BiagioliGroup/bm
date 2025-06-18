from odoo import http
from odoo.http import request
from io import BytesIO
import xlsxwriter

class LibroIVAController(http.Controller):

    @http.route('/descargar/libro_iva', type='http', auth='user')
    def descargar_libro_iva(self, **kwargs):
        active_ids = request.httprequest.args.get('ids')
        ids = [int(i) for i in active_ids.split(',') if i]

        comprobantes = request.env['comprobante.arca'].sudo().browse(ids)

        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet("Libro IVA")

        # Estilos
        header_format = workbook.add_format({
            'bold': True, 'bg_color': '#BDD7EE', 'border': 1, 'align': 'center'
        })
        money_format = workbook.add_format({'num_format': '$ #,##0.00', 'border': 1})
        text_format = workbook.add_format({'border': 1})
        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy', 'border': 1})
        bold_money = workbook.add_format({'num_format': '$ #,##0.00', 'bold': True, 'border': 1})
        bold_label = workbook.add_format({'bold': True, 'border': 1})

        # Encabezado
        headers = [
            "Fecha", "Tipo", "Número", "CUIT", "Razón Social", "Condición",
            "Imp. Neto Gravado", "IVA 21%", "Neto 10,5%", "IVA 10,5%", "Perc. IVA",
            "Perc. TEM", "Perc. IIBB", "Imp internos", "Exentos", "Total"
        ]
        sheet.write_row(0, 0, headers, header_format)

        row = 1
        for comp in comprobantes.filtered(lambda r: r.incluir_en_ddjj):
            sheet.write_datetime(row, 0, comp.fecha_emision, date_format)  # Fecha
            sheet.write(row, 1, comp.letra or '', text_format)              # Tipo
            sheet.write(row, 2, f"{comp.punto_venta}-{comp.nro_comprobante}", text_format)  # Número
            sheet.write(row, 3, comp.cuit_emisor or '', text_format)       # CUIT
            sheet.write(row, 4, comp.razon_social_emisor or '', text_format)  # Razón Social
            sheet.write(row, 5, "Responsable Inscripto", text_format)      # Condición
            sheet.write_number(row, 6, comp.importe_neto or 0, money_format)  # Imp. Neto Gravado
            sheet.write_number(row, 7, comp.iva_21 or 0, money_format)        # IVA 21%
            sheet.write_number(row, 8, comp.importe_neto_105 or 0, money_format)  # Neto 10.5%
            sheet.write_number(row, 9, comp.iva_105 or 0, money_format)         # IVA 10.5%
            sheet.write_number(row, 10, comp.perc_iva or 0, money_format)       # Perc. IVA
            sheet.write_number(row, 11, comp.perc_tem or 0, money_format)       # Perc. TEM
            sheet.write_number(row, 12, comp.perc_iibb or 0, money_format)      # Perc. IIBB
            sheet.write_number(row, 13, comp.imp_internos or 0, money_format)   # Imp internos
            sheet.write(row, 14, "", text_format)                                # Exentos (vacío)
            sheet.write_number(row, 15, comp.importe_total or 0, money_format)   # Total
            row += 1

        # Totales
        sheet.write(row, 5, "Totales", bold_label)
        sheet.write(row, 6, sum(c.importe_neto or 0 for c in comprobantes if c.incluir_en_ddjj), bold_money)
        sheet.write(row, 7, sum(c.iva_21 or 0 for c in comprobantes if c.incluir_en_ddjj), bold_money)
        sheet.write(row, 8, sum(c.importe_neto_105 or 0 for c in comprobantes if c.incluir_en_ddjj), bold_money)
        sheet.write(row, 9, sum(c.iva_105 or 0 for c in comprobantes if c.incluir_en_ddjj), bold_money)
        sheet.write(row, 10, sum(c.perc_iva or 0 for c in comprobantes if c.incluir_en_ddjj), bold_money)
        sheet.write(row, 11, sum(c.perc_tem or 0 for c in comprobantes if c.incluir_en_ddjj), bold_money)
        sheet.write(row, 12, sum(c.perc_iibb or 0 for c in comprobantes if c.incluir_en_ddjj), bold_money)
        sheet.write(row, 13, sum(c.imp_internos or 0 for c in comprobantes if c.incluir_en_ddjj), bold_money)
        sheet.write(row, 14, 0, bold_money)  # Exentos
        sheet.write(row, 15, sum(c.importe_total or 0 for c in comprobantes if c.incluir_en_ddjj), bold_money)

        workbook.close()
        output.seek(0)

        headers = [
            ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ('Content-Disposition', 'attachment; filename=libro_iva.xlsx')
        ]
        return request.make_response(output.read(), headers=headers)
