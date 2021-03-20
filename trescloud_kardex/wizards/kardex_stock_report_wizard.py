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
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)

STYLES = {
    'title': get_style(
        bold=True, font_name='Calibri', height=12, font_color=None,
        rotation=0, align='left', vertical='center', wrap=False,
        border=False, color=None, format=None
    ),
    'subtitle': get_style(
        bold=True, font_name='Calibri', height=10, font_color=None,
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
    'text_red': get_style(
        bold=False, font_name='Calibri', height=8, font_color=None,
        rotation=0, align=None, vertical='center', wrap=False,
        border=False, color='coral', format=None
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
    'number_red': get_style(
        bold=False, font_name='Calibri', height=8, font_color='white',
        rotation=0, align=None, vertical='center', wrap=False,
        border=False, color='coral', format='#,##0.00'
    ),
    'number_5': get_style(
        bold=False, font_name='Calibri', height=8, font_color=None,
        rotation=0, align=None, vertical='center', wrap=False,
        border=False, color=None, format='#,##0.00000'
    ),
    'number_5_red': get_style(
        bold=False, font_name='Calibri', height=8, font_color='white',
        rotation=0, align=None, vertical='center', wrap=False,
        border=False, color='coral', format='#,##0.00000'
    ),
    'number_6': get_style(
        bold=False, font_name='Calibri', height=8, font_color=None,
        rotation=0, align=None, vertical='center', wrap=False,
        border=False, color=None, format='#,##0.000000'
    ),
    'number_6_red': get_style(
        bold=False, font_name='Calibri', height=8, font_color='white',
        rotation=0, align=None, vertical='center', wrap=False,
        border=False, color='coral', format='#,##0.000000'
    ),
    'bold_number': get_style(
        bold=True, font_name='Calibri', height=8, font_color=None,
        rotation=0, align=None, vertical='center', wrap=False,
        border=False, color=None, format='#,##0.00'
    ),
    'bold_number_6': get_style(
        bold=True, font_name='Calibri', height=8, font_color=None,
        rotation=0, align=None, vertical='center', wrap=False,
        border=False, color=None, format='#,##0.000000'
    ),
    'text_null': get_style(
        bold=False, font_name='Calibri', height=8, font_color=None,
        rotation=0, align='center', vertical='center', wrap=False,
        border=False, color=None, format=None
    ),
    '_cost': get_style(
        bold=False, font_name='Calibri', height=8, font_color=None,
        rotation=0, align=None, vertical='center', wrap=False,
        border=False, color='yellow', format=None
    ),
    '_cost_number': get_style(
        bold=False, font_name='Calibri', height=8, font_color=None,
        rotation=0, align=None, vertical='center', wrap=False,
        border=False, color='yellow', format='#,##0.000000'
    ),
}


class KardexStockReportWizard(models.TransientModel):
    _name = 'kardex.stock.report.wizard'

    @api.model
    def _get_default_date_from(self):
        '''
        Metodo que obtiene la fecha inicial.
        '''
        date = fields.Date.from_string(fields.Date.context_today(self))
        date_from = '%s-%s-01' % (date.year, str(date.month).zfill(2))
        return date_from

    def _get_products(self):
        '''
        Metodo para obtener el sql de los productos a mostrar.
        '''
        sql = """SELECT p.id, tmpl.name 
                from product_product p
                join product_template tmpl on tmpl.id = p.product_tmpl_id where tmpl.type != 'service' """
        if self.product_id:
            sql += " and p.id in (%s) " % (','.join([str(item) for item in self.product_id.ids]))
        sql += """ order by tmpl.name """
        self.env.cr.execute(sql)
        products = self.env.cr.dictfetchall()
        return products

    def _get_cost_product(self, product_id, date_from=False, date_to=False, domain_extra=False, initial=False):
        '''
        Metodo que obtiene el costo promedio de un producto segun parametros indicados.
        El orden de al busqueda en "product_price_history" tiene inspiracion en metodo get_history_price
        y para cubrir el escenario MA-1633, donde: existe dos costos con misma fecha para el producto.
        '''
        domain = [('product_id', '=', product_id)]
        if date_from:
            domain += [('create_date', '>=', str(date_from))]
        if date_to:
            domain += [('create_date', '<=', str(date_to))]
        if domain_extra:
            domain += domain_extra
        if initial:
            cost = self.env['stock.valuation.layer'].sudo().search(domain, order='create_date DESC, id DESC', limit=1)
        else:
            cost = self.env['stock.valuation.layer'].sudo().search(domain, order='create_date DESC, id DESC')
        return cost

    def _get_product_qty(self, product_id, location_id=False, date_from=False, date_to=False):
        '''
        Metodo que obtiene la cantidad de productos segun los parametros indicados.
        '''
        sql = """select sum(quantity)
                 from stock_quant s
                 join product_product p on p.id = s.product_id 
                 where p.id = """+str(product_id)
        if date_from:
            sql += """ AND s.in_date >= '"""+str(date_from)+"""'"""
        if date_to:
            sql += """ AND s.in_date <= '"""+str(date_to)+"""'"""
        self.env.cr.execute(sql)
        total_open_qty = self.env.cr.dictfetchall()
        return total_open_qty[0]['sum'] or 0.0

    def _get_product_stock_record(self, product_id, date_from=False, date_to=False, domain_extra=False):
        '''
        Metodo que obtiene los registros de stock de un producto segun los parametros indicados.
        '''
        domain = [('product_id', '=', product_id)]
        if date_from:
            domain += [('date', '>=', str(date_from))]
        if date_to:
            domain += [('date', '<=', str(date_to))]
        if domain_extra:
            domain += domain_extra
        stock_product = self.env['stock.history'].sudo().search(domain, order='date,id')
        return stock_product

    date_from = fields.Date('Fecha desde', required=True, default=_get_default_date_from)
    date_to = fields.Date('Fecha hasta', required=True, default=fields.Date.today)
    product_id = fields.Many2many('product.product', string='Productos')

