# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import datetime, date
from xlwt import Workbook
import logging
from odoo.addons.general_reports.tools.xls_tools import get_style, cm2width
from odoo import models, fields, api
from pytz import timezone
import time
import pytz
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)

STYLES = {
    'title': get_style(
        bold=True, font_name='Calibri', height=12, font_color=None,
        rotation=0, align='center', vertical='center', wrap=False,
        border=False, color=None, format=None
    ),
    'header': get_style(
        bold=True, font_name='Calibri', height=8, font_color=None,
        rotation=0, align='center', vertical='center', wrap=False,
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


class StockHistory(models.TransientModel):
    _name = 'wizard.stock.history'

    def _get_filters(self):
        return [
            (u'Producto', u'Todos los productos' if not self.product_id else self.product_id.name),
            (u'Categoría', u'Todas las categorías' if not self.category_id else self.category_id.name),
            (u'Generado el', fields.Datetime.context_timestamp(self, datetime.now()).strftime('%Y-%m-%d %H:%M:%S'))
        ]

    def _get_columns_show(self):
        return [
            (u'CÓDIG0', 'default_code', 'text', 3.0),
            (u'PRODUCTO', 'name', 'text', 10),
            # (u'DIVISIÓN', 'product_tmpl_id.division_id.name', 'text', 5),
            (u'CATEGORÍA', 'product_tmpl_id.categ_id.name', 'text', 5),
        ]

    def get_all_data(self, group_by, where=''):
        '''
        Obtiene la cantidad en quants agrupado por producto
        '''
        tz_name = self._context.get('tz') or 'UTC'
        user_tz = timezone(tz_name)
        date = datetime.strptime('%s 23:59:59' % (self.date), DEFAULT_SERVER_DATETIME_FORMAT)
        # transformacion de la zona horaria utilizada (-5) a zona horaria UTC de la base de datos.
        # como ejemplo se obtendra:
        #  fecha hasta ingresado 31/03/2020 23:59:59 => fecha hasta obtenida 01/04/2020 04:59:59
        date = user_tz.localize(date).astimezone(pytz.utc)
        if self.product_id: where += ' and quant.product_id=%s ' % self.product_id.id
        if self.category_id: where += ' and template.categ_id=%s ' % self.category_id.id
        if self.date: where += " and quant.in_date <= '%s' " % str(date)
        sql = "select " + group_by + ", sum(quantity) "\
                            "from stock_quant quant join product_product product on product.id=quant.product_id "\
                            "	join product_template template on template.id=product.product_tmpl_id " \
                            "	join stock_location location on location.id=quant.location_id "\
                            "where location.usage='internal' and quant.company_id=%s " + where + " "\
                            "group by " + group_by + " "\
                            "having sum(quantity) <> 0.00"
        self.env.cr.execute(sql, (self.env.user.company_id.id,))
        return self.env.cr.fetchall()

    def __get_data(self):
        class Virtual(object):
            def __init__(self, product, quantity, unit_price):
                self.product = product
                self.quantity = quantity
                cost = unit_price and unit_price.unit_cost or 0.0
                self.unit_price =cost
                self.inventory_value = quantity * cost
        tz_name = self._context.get('tz') or 'UTC'
        user_tz = timezone(tz_name)
        date_to = datetime.strptime('%s 23:59:59' % (self.date), DEFAULT_SERVER_DATETIME_FORMAT)
        # transformacion de la zona horaria utilizada (-5) a zona horaria UTC de la base de datos.
        # como ejemplo se obtendra:
        #  fecha hasta ingresado 31/03/2020 23:59:59 => fecha hasta obtenida 01/04/2020 04:59:59
        date_to = user_tz.localize(date_to).astimezone(pytz.utc)
        res, data = {}, self.get_all_data('quant.product_id')
        i = 0
        kardex = self.env['kardex.stock.report.wizard']
        for product_id, qty in data:
            i += 1
            product = self.env['product.product'].browse(product_id)
            _logger.info("Producto No. %s - %s" % (i, product.name))
            if not product.id in res:
                price = kardex._get_cost_product(product.id, date_to=date_to, initial=True)
            res[product] = Virtual(product, qty, price)
        sortDic = sorted(res.items())
        return sortDic

    product_id = fields.Many2one('product.product', 'Producto')
    date = fields.Date(string='Fecha', default=fields.Date.today())
    category_id = fields.Many2one('product.category', 'Categoría')

    def generate_excel(self):
        self.ensure_one()
        book = Workbook(encoding='UTF-8')
        sheet = book.add_sheet('Hoja 1')
        sheet.show_grid = False
        sheet.write_merge(0, 0, 0, 2, self.env.user.company_id.name, STYLES['title'])
        sheet.write_merge(1, 1, 0, 2, u'Valoración de existencias', STYLES['title'])
        row_ini, col_ini = 3, 0
        for key, value in self._get_filters():
            sheet.write(row_ini, 0, key, STYLES['bold_text'])
            sheet.write(row_ini, 1, value, STYLES['text'])
            row_ini += 1
        columns = self._get_columns_show()
        for col, (key, value, style, size) in enumerate(columns, col_ini):
            sheet.write(row_ini+1, col, key, STYLES['header'])
            if size: sheet.col(col).width = cm2width(size)
        sheet.write(row_ini+1, col_ini+len(columns), u'CANTIDAD', STYLES['header'])
        sheet.write(row_ini+1, col_ini+len(columns)+1, u'PRECIO UNITARIO', STYLES['header'])
        sheet.write(row_ini+1, col_ini+len(columns)+2, u'TOTAL INVENTARIO', STYLES['header'])
        sheet.col(col_ini+len(columns)+1).width = cm2width(3.5)
        sheet.col(col_ini+len(columns)+2).width = cm2width(3.5)
        sheet.col(col_ini+len(columns)+3).width = cm2width(3.5)
        inventories = self.__get_data()
        quantity = inventory_value = 0.0
        for product, line in inventories:
            sheet.row(row_ini+2).level = 1
            for col, (key, value, style, size) in enumerate(columns, col_ini):
                sheet.write(row_ini+2, col, valuation(product, value) or '', STYLES[style])
            sheet.write(row_ini+2, col_ini+len(columns), line.quantity, STYLES['number'])
            sheet.write(row_ini+2, col_ini+len(columns)+1, line.unit_price, STYLES['number_6'])
            sheet.write(row_ini+2, col_ini+len(columns)+2, line.inventory_value, STYLES['number'])
            quantity, inventory_value = quantity + line.quantity, inventory_value + line.inventory_value
            row_ini += 1
        sheet.write(row_ini + 2, col_ini, 'TOTAL:', STYLES['bold_number'])
        sheet.write(row_ini+2, col_ini+len(columns), quantity, STYLES['bold_number'])
        sheet.write(row_ini+2, col_ini+len(columns)+2, inventory_value, STYLES['bold_number'])
        return self.env['base.file.report'].show_excel(book, u'Valoración de existencias.xls')
