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

        headers = [
            "Fecha", "Tipo", "Número", "CUIT", "Razón Social", "Condición",
            "Imp. Neto Gravado", "IVA 21%", "Neto 10,5%", "IVA 10,5%", "Perc. IVA",
            "Perc. TEM", "Perc. IIBB", "Imp internos", "Exentos", "Total"
        ]
        sheet.write_row(0, 0, headers, header_format)

        row = 1
        for comp in comprobantes.filtered(lambda r: r.incluir_en_ddjj):
            sheet.write_datetime(row, 0, comp.fecha_emision, date_format)
            sheet.write(row, 1, comp.letra or '', text_format)
            sheet.write(row, 2, f"{comp.punto_venta}-{comp.nro_comprobante}", text_format)
            sheet.write(row, 3, comp.cuit_emisor or '', text_format)
            sheet.write(row, 4, comp.razon_social_emisor or '', text_format)
            sheet.write(row, 5, "Responsable Inscripto", text_format)
            sheet.write_number(row, 6, comp.importe_neto or 0, money_format)
            sheet.write_number(row, 7, comp.iva or 0, money_format)
            sheet.write(row, 8, "", text_format)  # Neto 10,5%
            sheet.write(row, 9, "", text_format)  # IVA 10,5%
            sheet.write_number(row, 10, comp.perc_iva or 0, money_format)
            sheet.write_number(row, 11, comp.perc_tem or 0, money_format)
            sheet.write_number(row, 12, comp.perc_iibb or 0, money_format)
            sheet.write_number(row, 13, comp.imp_internos or 0, money_format)
            sheet.write(row, 14, "", text_format)  # Exentos
            sheet.write_number(row, 15, comp.importe_total or 0, money_format)
            row += 1

            # ⬇️ Después del bucle for comp in comprobantes...
            # Sumamos totales
            total_neto = sum(comp.importe_neto for comp in comprobantes if comp.incluir_en_ddjj)
            total_iva = sum(comp.iva for comp in comprobantes if comp.incluir_en_ddjj)
            total_iva_105 = sum(0 for comp in comprobantes if comp.incluir_en_ddjj)  # si luego se usa
            total_perc_iva = sum(comp.percepcion_iva for comp in comprobantes if comp.incluir_en_ddjj)
            total_perc_iibb = sum(comp.percepcion_iibb for comp in comprobantes if comp.incluir_en_ddjj)
            total_muni = sum(comp.impuesto_municipal for comp in comprobantes if comp.incluir_en_ddjj)
            total_internos = sum(comp.impuesto_interno for comp in comprobantes if comp.incluir_en_ddjj)
            total_exentos = sum(0 for comp in comprobantes if comp.incluir_en_ddjj)
            total_total = sum(comp.importe_total for comp in comprobantes if comp.incluir_en_ddjj)

            # Formato negrita
            bold_money = workbook.add_format({'num_format': '$ #,##0.00', 'bold': True})
            bold_label = workbook.add_format({'bold': True})

            sheet.write(row, 6, total_neto, bold_money)
            sheet.write(row, 7, total_iva, bold_money)
            sheet.write(row, 8, total_iva_105, bold_money)
            sheet.write(row, 9, 0, bold_money)  # si luego agregás IVA 10.5%
            sheet.write(row, 10, total_perc_iva, bold_money)
            sheet.write(row, 11, total_muni, bold_money)
            sheet.write(row, 12, total_perc_iibb, bold_money)
            sheet.write(row, 13, total_internos, bold_money)
            sheet.write(row, 14, total_exentos, bold_money)
            sheet.write(row, 15, total_total, bold_money)

        workbook.close()
        output.seek(0)

        headers = [
            ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ('Content-Disposition', 'attachment; filename=libro_iva.xlsx')
        ]
        return request.make_response(output.read(), headers=headers)
