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
        sheet.write_row(0, 0, ["Fecha", "Proveedor", "CUIT", "Total", "Neto", "IVA"])  # ajustar columnas
        row = 1
        for comp in comprobantes.filtered(lambda r: r.incluir_en_ddjj):
            sheet.write_row(row, 0, [
                comp.fecha_emision.strftime('%d/%m/%Y'),
                comp.razon_social_emisor,
                comp.cuit_emisor,
                comp.importe_total,
                comp.importe_neto,
                comp.iva,
            ])
            row += 1
        workbook.close()
        output.seek(0)

        headers = [
            ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ('Content-Disposition', 'attachment; filename=libro_iva.xlsx')
        ]
        return request.make_response(output.read(), headers=headers)
