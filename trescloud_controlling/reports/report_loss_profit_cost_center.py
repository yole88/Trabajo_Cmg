# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import datetime, date, timedelta
from pytz import timezone
from xlwt import Workbook
from odoo.addons.general_reports.tools.xls_tools import get_style, cm2width
#from odoo.addons.l10n_ec.models.auxiliar_functions import convert_datetime_to_ECT
from calendar import monthrange

STYLES = {
    'title': get_style(
        bold=True, font_name='Calibri', height=12, font_color=None,
        rotation=0, align='left', vertical='center', wrap=False,
        border=False, color=None, format=None
    ),
    'title1': get_style(
        bold=True, font_name='Calibri', height=8, font_color=None,
        rotation=0, align='left', vertical='center', wrap=False,
        border=False, color=None, format=None
    ),
    'header': get_style(
        bold=True, font_name='Calibri', height=8, font_color=None,
        rotation=0, align='center', vertical='center', wrap=True,
        border=True, color=None, format=None
    ),
    'text': get_style(
        bold=False, font_name='Calibri', height=8, font_color=None,
        rotation=0, align=None, vertical='center', wrap=False,
        border=False, color=None, format=None
    ),
    'bold_text': get_style(
        bold=True, font_name='Calibri', height=8, font_color=None,
        rotation=0, align=None, vertical='center', wrap=False,
        border=False, color=None, format=None
    ),
    'number': get_style(
        bold=False, font_name='Calibri', height=8, font_color=None,
        rotation=0, align=None, vertical='center', wrap=False,
        border=False, color=None, format='#,##0.00'
    ),
    'bold_number': get_style(
        bold=True, font_name='Calibri', height=8, font_color=None,
        rotation=0, align=None, vertical='center', wrap=False,
        border=False, color=None, format='#,##0.00'
    )
}


class ReportLossProfitCostCenter(models.TransientModel):
    _name = 'report.loss.profit.cost.center'
    _description = "Report center cost"

    def generate_report_xls(self, data):
        '''
        Este metodo genera el reporte de perdidas y ganancias por centros de costos
        '''
        book = Workbook(encoding='UTF-8')
        sheet = book.add_sheet('Hoja1')
        sheet.show_grid = False
        columns = [
            (u'CUENTA', 3.5),
            (u'NOMBRE DE LA CUENTA', 10.0)
        ]
        month = {
            u'01': u'ENE',
            u'02': u'FEB',
            u'03': u'MAR',
            u'04': u'ABR',
            u'05': u'MAY',
            u'06': u'JUN',
            u'07': u'JUL',
            u'08': u'AGO',
            u'09': u'SEP',
            u'10': u'OCT',
            u'11': u'NOV',
            u'12': u'DIC'
        }
        #Se obtienen los periodos para completar los nombre de las columnas
        date_start = data.get('date_start')
        date_end = data.get('date_end')
        detail_by_period = data.get('detail_by_period')
        include_archived = data.get('include_archived')
        start = datetime.strftime(date_start, "%Y-%m-%d")
        end = datetime.strftime(date_end, "%Y-%m-%d")
        split_date_start = start.split('-')
        split_date_end = end.split('-')
        periods = []
        if detail_by_period:
            if int(split_date_start[0]) == int(split_date_end[0]):
                for r in range(int(split_date_start[1]), int(split_date_end[1]) + 1):
                    col_name = month[str(r).zfill(2)] + '/' + split_date_start[0]
                    columns.append((col_name, 3.0))
                    #Se tiene en cuenta la fecha la fecha de inicio y fin, no siempre son el primer y ultimo dia del mes
                    if r == 1: #Primer periodo
                        tmp = monthrange(int(split_date_start[0]), int(split_date_start[1]))
                        periods.append((date_start, split_date_start[0]+ '-' + split_date_start[1] + '-' + str(tmp[1])))
                    elif r == int(split_date_end[1]): #Ultimo periodo
                        periods.append((split_date_end[0]+ '-' + split_date_end[1] + '-01', date_end))
                    else:
                        tmp = monthrange(int(split_date_start[0]), r)
                        periods.append((split_date_start[0]+ '-' + str(r).zfill(2) + '-01', split_date_start[0]+ '-' + str(r).zfill(2) + '-' + str(tmp[1]).zfill(2)))
            else:
                month_start = int(split_date_start[1])
                month_stop = int(split_date_end[1]) + 1
                annio_start = int(split_date_start[0])
                annio_stop = int(split_date_end[0])
                count = 1
                while(month_start != month_stop or annio_start != annio_stop):
                    col_name = month[str(month_start).zfill(2)] + '/' + str(annio_start)
                    columns.append((col_name, 3.0))
                    tmp = monthrange(annio_start, month_start)
                    #Se tiene en cuenta la fecha la fecha de inicio y fin, no siempre son el primer y ultimo dia del mes
                    if count == 1: #Primer periodo
                        periods.append((date_start, str(annio_start) + '-' + str(month_start) + '-' + str(tmp[1])))
                    elif month_start == month_stop - 1 and annio_start == annio_stop: #Ultimo periodo
                        periods.append((str(annio_start) + '-' + str(month_start).zfill(2) + '-01', date_end))
                    else:
                        periods.append((str(annio_start) + '-' + str(month_start).zfill(2) + '-01', str(annio_start) + '-' + str(month_start).zfill(2) + '-' + str(tmp[1])))
                    count += 1
                    if month_start == 12:
                        month_start = 1
                        annio_start += 1
                    else:
                        month_start += 1
        else:
            col_name = month[split_date_start[1]] + '/' + split_date_start[0] + ' - ' + month[split_date_end[1]] + '/' + split_date_end[0]
            columns.append((col_name, 3.0))
            periods.append((date_start, date_end))
        #Se obtienen los centros de costos que se van a analizar
        analytic_ids = data.get('analytic_ids')
        if analytic_ids:
            analytics = self.env['account.analytic.account'].browse(analytic_ids)
        else:
            analytics = self.get_all_analytics(include_archived)
        #Se escribe la cabecera del reporte
        columns.append((u'TOTAL', 3.0))
        company = self.env.user.company_id
        sheet.write(0, 0, company.name, STYLES['title'])
        sheet.write(1, 0, u'Balance de Resultados', STYLES['title'])
        sheet.write(2, 0, u'Rango: ' + datetime.strftime(datetime.strptime(start, '%Y-%m-%d'), '%d/%m/%Y') + u' - ' + datetime.strftime(datetime.strptime(end, '%Y-%m-%d'), '%d/%m/%Y'), STYLES['title1'])
        sheet.write(3, 0, u'Generado el: ' + fields.Datetime.context_timestamp(self, datetime.now()).strftime('%Y-%m-%d %H:%M:%S'), STYLES['title1'])
        sheet.write(4, 0, u'Generado por: ' + self.env.user.name, STYLES['title1'])
        #Se escriben las cabeceras de columnas(1mer nivel)
        row_ini, col_ini = 6, 0
        col_period = 2
        qty_analytics = len(analytics) - 1
        for col, (name, size) in enumerate(columns, col_ini):
            if name in [u'CUENTA', u'NOMBRE DE LA CUENTA']:
                sheet.write_merge(row_ini, row_ini + 2, col, col, name, STYLES['header'])
                sheet.row(row_ini).height_mismatch = True
                sheet.row(row_ini).height = 256 * 1
                if size: sheet.col(col).width = cm2width(size)
            elif name in [u'TOTAL']:
                sheet.write_merge(row_ini, row_ini + 2, col_period, col_period, name, STYLES['header'])
                sheet.row(row_ini).height_mismatch = True
                sheet.row(row_ini).height = 256 * 1
                if size: sheet.col(col_period).width = cm2width(size)
            else:
                sheet.write_merge(row_ini, row_ini, col_period, col_period + qty_analytics, name, STYLES['header'])
                sheet.row(row_ini).height_mismatch = True
                sheet.row(row_ini).height = 256 * 1
                if size: sheet.col(col_period).width = cm2width(size)
                col_period += qty_analytics + 1
        #Se escriben las cabeceras de columnas(2mer nivel)
        col = 2
        for period in periods:
            for analytic in analytics:
                sheet.write_merge(row_ini + 1, row_ini + 2, col, col, analytic.name, STYLES['header'])
                sheet.row(row_ini).height_mismatch = True
                sheet.row(row_ini).height = 256 * 1
                if size: sheet.col(col).width = cm2width(size)
                col += 1
        # #Se escriben los datos del reporte
        f = 3
        for id, line in self.get_data(periods, analytics):
            c = 2
            if line[4] == 'view':
                sheet.write(row_ini + f, 0, line[0], style=STYLES['bold_text'])
                sheet.write(row_ini + f, 1, line[1], style=STYLES['bold_text'])
                for i in range(0, len(line[2])):
                    sheet.write(row_ini + f, c, line[2][i], style=STYLES['bold_number'])
                    c += 1
                sheet.write(row_ini + f, c, line[3], style=STYLES['bold_number'])
            elif line[0] == u'9999999999':
                f += 1
                sheet.write(row_ini + f, 1, line[1], style=STYLES['bold_text'])
                for i in range(0, len(line[2])):
                    sheet.write(row_ini + f, c, line[2][i], style=STYLES['bold_number'])
                    c += 1
                sheet.write(row_ini + f, c, line[3], style=STYLES['bold_number'])
            else:
                sheet.write(row_ini + f, 0, line[0], style=STYLES['text'])
                sheet.write(row_ini + f, 1, line[1], style=STYLES['text'])
                for i in range(0, len(line[2])):
                    sheet.write(row_ini + f, c, line[2][i], style=STYLES['number'])
                    c += 1
                sheet.write(row_ini + f, c, line[3], style=STYLES['number'])
            f += 1
        return self.env['base.file.report'].show_excel(book, u'Reporte de pérdidas y ganancias.xls')

    def get_data(self, periods, analytics):
        '''
        Este metodo devuelve las lineas del reporte
        '''
        def get_account_hierarchy(self, account):
            if account.id:
                if account.id not in all_account_ids:
                    all_account_ids.append(account.id)
                    all_parent_account_ids.append(account.id)
            return all_account_ids

        data = {}
        self.env.cr.execute('''
            select
                distinct aa.id
            from account_analytic_line aal join
                account_account aa
                    on aal.general_account_id=aa.id
            where date>=%s and date<=%s and account_id in %s
        ''', (periods[0][0], periods[-1][1], tuple(analytics.ids)))
        accounts = self.env.cr.dictfetchall()
        all_account_ids = []
        all_parent_account_ids = []
        for account in accounts:
            get_account_hierarchy(self, self.env['account.account'].browse(account.get('id')))
        for account_id in all_account_ids:
            account = self.env['account.account'].browse(account_id)
            account_id = account.id
            account_code = account.code
            account_name = account.name
            account_ids = self.env['account.account'].search([('id', '=', account_id)]).ids
            for period in periods:
                for analytic in analytics:
                    self.env.cr.execute('''
                        select
                            coalesce(sum(amount), 0) as amount
                        from account_analytic_line
                        where date>=%s and date<=%s and account_id=%s and general_account_id in %s
                    ''', (period[0], period[1], analytic.id, tuple(account_ids)))
                    records = self.env.cr.dictfetchall()
                    for record in records:
                        amount = record.get('amount')
                        data.setdefault(account_id, [account_code, account_name, [], 0, u''])
                        data[account_id][2].append(amount)
                        data[account_id][3] += amount
                        data[account_id][4] = account.user_type_id.type
        account_ids = self.env['account.account'].search([('id', '=', all_parent_account_ids)]).ids
        if account_ids:
            for period in periods:
                for analytic in analytics:
                    self.env.cr.execute('''
                        select
                            coalesce(sum(amount), 0) as amount
                        from account_analytic_line
                        where date>=%s and date<=%s and account_id=%s and general_account_id in %s
                    ''', (period[0], period[1], analytic.id, tuple(account_ids)))
                    records = self.env.cr.dictfetchall()
                    for record in records:
                        amount = record.get('amount')
                        data.setdefault(9999999999, [u'9999999999', u'UTILIDAD O PÉRDIDA DEL EJERCICIO', [], 0, u''])
                        data[9999999999][2].append(amount)
                        data[9999999999][3] += amount
        sortDic = sorted(data.items())
        return sortDic

    def get_all_analytics(self, include_archived):
        '''
        Metodo hook para obtener todas las cuentas analiticas
        '''
        analytic_account_ids = []
        if include_archived:
            analytic_account = self.env['account.analytic.account'].search([], order='name')
            analytic_account.filtered(lambda a: a.active == True and a.active == False)
        else:
            analytic_account = self.env['account.analytic.account'].search([], order='name')
            analytic_account.filtered(lambda a: a.active == True)
        for record in analytic_account:
            analytic_account_ids.append(record.id)
        return self.env['account.analytic.account'].browse(analytic_account_ids)
