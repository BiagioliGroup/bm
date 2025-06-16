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
            sheet.write_number(row, 10, comp.percepcion_iva or 0, money_format)
            sheet.write_number(row, 11, comp.impuesto_municipal or 0, money_format)
            sheet.write_number(row, 12, comp.percepcion_iibb or 0, money_format)
            sheet.write_number(row, 13, comp.impuesto_interno or 0, money_format)
            sheet.write(row, 14, "", text_format)  # Exentos
            sheet.write_number(row, 15, comp.importe_total or 0, money_format)
            row += 1

        workbook.close()
        output.seek(0)

        headers = [
            ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ('Content-Disposition', 'attachment; filename=libro_iva.xlsx')
        ]
        return request.make_response(output.read(), headers=headers)
