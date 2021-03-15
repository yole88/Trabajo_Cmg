# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import datetime, date,timedelta
from xlwt import Workbook, Formula
from odoo.addons.general_reports.tools.xls_tools import get_style, GET_LETTER, cm2width
from odoo.exceptions import ValidationError
from pytz import timezone
import time
import pytz
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import itertools
import operator
import logging
_logger = logging.getLogger(__name__)

STYLES = {
    'title': get_style(
        bold=True, font_name='Calibri', height=12, font_color=None,
        rotation=0, align='center', vertical='center', wrap=False,
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
    'number_6': get_style(
        bold=False, font_name='Calibri', height=8, font_color=None,
        rotation=0, align=None, vertical='center', wrap=False,
        border=False, color=None, format='#,##0.000000'
    ),
    'bold_number': get_style(
        bold=True, font_name='Calibri', height=8, font_color=None,
        rotation=0, align=None, vertical='center', wrap=False,
        border=False, color=None, format='#,##0.00'
    ),
}


def valuation(object, fields):
    field, sep, fields = fields.partition('.')
    object = getattr(object, field)
    if fields:
         object = valuation(object, fields)
    return object


class InventoryTrialBalanceWizard(models.TransientModel):
    _name = 'inventory.trial.balance.report.wizard'

    def _get_account_report(self):
        '''
        Obtiene por defecto las cuentas contables a utilizar en el
        reporte
        '''
        company_id = self.env.user.company_id
        return company_id.inv_trial_balance_account_ids

    def _get_filters(self):
        date_start = self.date_from.strftime("%Y-%m-%d")
        date_end = self.date_to.strftime("%Y-%m-%d")
        return [
            (u'Producto', u'Todos los productos' if not self.product_id else self.product_id.name),
            (u'Categoría', u'Todas las categorías' if not self.category_id else self.category_id.name),
            (u'Generado el', fields.Datetime.context_timestamp(self, datetime.now()).strftime('%Y-%m-%d %H:%M:%S')),
            (u'Fecha inicio', date_start),
            (u'Fecha fin', date_end)
        ]

    def _get_columns_show(self):
        return [
            (u'CÓDIG0', 'default_code', 'text', 3.0),
            (u'PRODUCTO', 'name', 'text', 10),
            (u'CATEGORÍA', 'product_tmpl_id.categ_id.name', 'text', 5),
        ]

    @api.model
    def get_balance_account(self, date_from, date_to):
        '''
        Funcion para obtener sumatoria de Debitos y Creditos de cuenta contables.
        '''
        where = ''
        where_previous = ''
        if self.product_id:
            where += ' and l.product_id=%s ' % self.product_id.id
            where_previous += ' and l.product_id=%s ' % self.product_id.id
        if self.category_id:
            where += ' and template.categ_id=%s ' % self.category_id.id
            where_previous += ' and template.categ_id=%s ' % self.category_id.id
        where += " and am.date <= '%s' " % str(date_to)
        where_previous += " and am.date < '%s' " % str(date_from)
        ids_account = []
        if self.account_ids:
            ids_account = self.account_ids.ids
        else:
            raise ValidationError(u'Por favor ingrese al menos una cuenta contable o configure las cuentas contables por defecto para'
                                  u' el balance de comprobación inventario. \n\n'
                                  u' Para configurar las cuentas contables por defecto ingrese al menú Configuración > Usuarios > Compañías, seleccione la compañía y'
                                  u' en la pestaña configuraciones ecuatorianas busque el campo "Balance de comprobación inventario"')
        sql = '''
        with data_previus as (
            select l.product_id,  COALESCE(SUM(debit),0) - COALESCE(SUM(credit),0) amount
            from account_move am 
                JOIN account_move_line l on am.id=l.move_id
                JOIN account_account acc ON l.account_id = acc.id
                JOIN product_product product on product.id=l.product_id 
                JOIN product_template template on template.id=product.product_tmpl_id 
            where 
             l.account_id in %(account_account)s
            %(strwhereprevious)s
            group by l.product_id
        )
        select l.product_id,  
                max(dp.amount) as amount_previous,
                COALESCE(SUM(debit),0) - COALESCE(SUM(credit),0) amount
            from account_move am 
                JOIN account_move_line l on am.id=l.move_id
                JOIN account_account acc ON l.account_id = acc.id 
                JOIN product_product product on product.id=l.product_id 
                JOIN product_template template on template.id=product.product_tmpl_id 
                left join data_previus dp on dp.product_id = l.product_id
                --JOIN stock_picking sp on sp.account_move_id  = am.id
            where
            l.account_id in %(account_account)s
            %(strwhere)s
            group by l.product_id
        '''%{
                'strwhereprevious': where_previous,
                'account_account': len(ids_account) > 1 and tuple(ids_account) or '(%s)'%(ids_account[0]),
                'strwhere': where
        }
        self.env.cr.execute(sql)
        res = self.env.cr.fetchall()
        return res

    def get_all_data(self, date_from, date_to):
        '''
        Obtiene la cantidad en quants agrupado por producto
        '''
        group_by = 'quant.product_id'
        where = ''
        if self.product_id: where += ' and quant.product_id=%s ' % self.product_id.id
        if self.category_id: where += ' and template.categ_id=%s ' % self.category_id.id
        where += " and quant.in_date <= '%s' " % str(date_to)
        sql = '''
        with data_history as (
            select %(group_by)s, sum(quantity)  qty_history
                from stock_quant quant 
                    join product_product product on product.id=quant.product_id 
                    join product_template template on template.id=product.product_tmpl_id 
                    join stock_location location on location.id=quant.location_id 
                where location.usage='internal' and quant.company_id=1 
                and quant.in_date < '%(date_from)s'
                group by  quant.product_id
                having sum(quantity) <> 0.00
        )
        select
        %(group_by)s, max(dah.qty_history), sum(quant.quantity)
        from stock_quant quant 
            join product_product product on product.id=quant.product_id 
            join product_template template on template.id=product.product_tmpl_id 
            join stock_location location on location.id=quant.location_id 
            left join data_history dah on dah.product_id = quant.product_id
        where location.usage='internal' and quant.company_id=%(company)s
        %(strwhere)s
        group by  %(group_by)s
        having sum(quantity) <> 0.00;
        ''' %{
                'date_from': str(date_from),
                'company': self.env.user.company_id.id,
                'strwhere': where,
                'group_by': group_by
            }

        self.env.cr.execute(sql)
        return self.env.cr.fetchall()

    def __get_data(self):
        '''
        Obtiene los datos que seran presentados en el reporte.
        '''
        class Virtual(object):
            def __init__(self, product, quantity, qty_old, unit_price, unit_price_history,
                         account_value, previous_account_value):
                #Declaracion del objeto se agregan los valores del kardex y contabilidad.
                self.product = product
                #self.quantity = quantity
                cost = unit_price and unit_price.unit_cost or 0.0
                cost_old = unit_price_history and unit_price_history.unit_cost or 0.00
                qty_old = qty_old and qty_old or 0.00
                #self.unit_price =cost
                self.inventory_value = quantity * cost
                self.history_inventory_value = qty_old * cost_old
                self.account_value = account_value
                self.previous_account_value = previous_account_value
        #transformacion de zona horaria
        tz_name = self._context.get('tz') or 'UTC'
        user_tz = timezone(tz_name)
        date_from = datetime.strptime('%s 00:00:00' % (self.date_from), DEFAULT_SERVER_DATETIME_FORMAT)
        date_from = user_tz.localize(date_from).astimezone(pytz.utc)
        date_to = datetime.strptime('%s 23:59:59' % (self.date_to), DEFAULT_SERVER_DATETIME_FORMAT)
        date_to = user_tz.localize(date_to).astimezone(pytz.utc)
        #datos de cantidades y productos del quant
        res, data = {}, self.get_all_data(date_from, date_to)
        #montos de la contabilidad segun los apuntes contables, no es necesario convertir las fechas con la zona horaria.
        #el campo fecha del asiento contable es de tipo fecha (date).
        data_account = self.get_balance_account(self.date_from, self.date_to)
        #convierte la lista de tuplas en diccionario con product_id como la clave
        #quedando {'product_id': {'vals': [monto previo, monto actual]}}
        dict_account = {key: {'vals': [v[1], v[2]] for v in vals} for key, vals in itertools.groupby(sorted(data_account), key=operator.itemgetter(0))}
        i = 0
        kardex = self.env['kardex.stock.report.wizard']
        for product_id, qty_previous, qty in data:
            i += 1
            #obtiene del diccionario el valor que corresponde contablemente.
            value_account = dict_account.get(product_id)
            list_acount = value_account and value_account.get('vals', []) or []
            product = self.env['product.product'].browse(product_id)
            _logger.info("Producto No. %s - %s" % (i, product.name))
            #if not res.has_key(product.id):
            if not product.id in res:
                #obtine el costo unitario segun fecha ingresada
                price = kardex._get_cost_product(product.id, date_to=date_to, initial=True)
                price_previous = kardex._get_cost_product(product.id, date_to=date_from, initial=True)
            account_value = list_acount and list_acount[1] or 0.00
            previous_account_value = list_acount and list_acount[0] or 0.00
            res[product] = Virtual(product, qty, qty_previous, price, price_previous, account_value, previous_account_value)
         #res.sort(key=lambda (key, val): key.name)
        sortDic = sorted(res.items())
        return sortDic

    product_id = fields.Many2one('product.product', 'Producto')
    date_from = fields.Date(string='Fecha inicio', required=True)
    date_to = fields.Date(string='Fecha fin', required=True)
    category_id = fields.Many2one('product.category', 'Categoría')
    account_ids = fields.Many2many('account.account', string='Cuentas contables',
                                   default=_get_account_report)

    def generate_excel(self):
        self.ensure_one()
        timestr = time.strftime("%Y%m%d-%H%M%S")
        book = Workbook(encoding='UTF-8')
        sheet = book.add_sheet('Hoja 1')
        sheet.show_grid = False
        sheet.write_merge(0, 0, 0, 2, self.env.user.company_id.name, STYLES['title'])
        sheet.write_merge(1, 1, 0, 2, u'Balance de comprobación inventario (Dólares)', STYLES['title'])
        row_ini, col_ini = 3, 0
        for key, value in self._get_filters():
            sheet.write(row_ini, 0, key, STYLES['bold_text'])
            sheet.write(row_ini, 1, value, STYLES['text'])
            row_ini += 1
        columns = self._get_columns_show()
        for col, (key, value, style, size) in enumerate(columns, col_ini):
            sheet.write(row_ini+1, col, key, STYLES['header'])
            if size: sheet.col(col).width = cm2width(size)
        row_heard = row_ini+1
        col_heard = col_ini+len(columns)
        sheet.write(row_heard, col_heard, u'SALDO ANTERIOR KARDEX', STYLES['header'])
        sheet.write(row_heard, col_heard+1, u'MOVIMIENTOS KARDEX', STYLES['header'])
        sheet.write(row_heard, col_heard+2, u'SALDO ACTUAL KARDEX', STYLES['header'])
        sheet.write(row_heard, col_heard+3, u'SALDO ANTERIOR CONTABILIDAD', STYLES['header'])
        sheet.write(row_heard, col_heard+4, u'MOVIMIENTOS CONTABILIDAD', STYLES['header'])
        sheet.write(row_heard, col_heard+5, u'SALDO ACTUAL CONTABILIDAD', STYLES['header'])
        sheet.write(row_heard, col_heard+6, u'DIFERENCIA SALDO ANTERIOR', STYLES['header'])
        sheet.write(row_heard, col_heard+7, u'DIFERENCIA MOVIMIENTOS', STYLES['header'])
        sheet.write(row_heard, col_heard+8, u'DIFERENCIA SALDO ACTUAL' , STYLES['header'])

        sheet.col(col_heard+1).width = cm2width(3.5)
        sheet.col(col_heard+2).width = cm2width(3.5)
        sheet.col(col_heard+3).width = cm2width(3.5)
        sheet.col(col_heard+4).width = cm2width(3.5)
        sheet.col(col_heard+5).width = cm2width(3.5)
        sheet.col(col_heard+6).width = cm2width(3.5)
        sheet.col(col_heard+7).width = cm2width(3.5)
        sheet.col(col_heard+8).width = cm2width(3.5)
        sheet.row(row_heard).height = cm2width(0.50)
        inventories = self.__get_data()
        quantity = inventory_value = 0.0
        for product, line in inventories:
            sheet.row(row_ini+2).level = 1
            for col, (key, value, style, size) in enumerate(columns, col_ini):
                sheet.write(row_ini+2, col, valuation(product, value) or '', STYLES[style])
            column = col_ini + len(columns)
            row = row_ini + 2
            sheet.write(row, column, line.history_inventory_value, STYLES['number'])
            sheet.write(row, column+1,
                        Formula('%s%s - %s%s' % (GET_LETTER(column+2), row_ini+3,
                                                 GET_LETTER(column), row_ini+3)
                        ), STYLES['number'])
            sheet.write(row, column+2, line.inventory_value, STYLES['number'])
            sheet.write(row, column+3, line.previous_account_value, STYLES['number'])
            sheet.write(row, column+4, Formula('%s%s - %s%s' % (
                                                GET_LETTER(column+5), row_ini+3,
                                                GET_LETTER(column+3), row_ini+3)
                        )
                        ,STYLES['number'])
            sheet.write(row, column+5, line.account_value, STYLES['number'])
            sheet.write(row, column+6,
                        Formula('%s%s - %s%s' % (GET_LETTER(column), row_ini+3,
                                                 GET_LETTER(column+3), row_ini+3)
                        ), STYLES['number'])
            sheet.write(row, column+7,
                        Formula('%s%s - %s%s' % (GET_LETTER(column+1), row_ini+3,
                                                 GET_LETTER(column+4), row_ini+3)
                        ), STYLES['number'])
            sheet.write(row, column+8,
                        Formula('%s%s - %s%s' % (GET_LETTER(column+2), row_ini+3,
                                                 GET_LETTER(column+5), row_ini+3)
                        ), STYLES['number'])
            quantity, inventory_value = quantity + 0, inventory_value + line.inventory_value
            row_ini += 1
        
        return self.env['base.file.report'].show_excel(book, u'Balance de comprobación inventario.xls')