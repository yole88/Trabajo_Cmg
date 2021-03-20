# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    financial_responsible_id = fields.Many2one('hr.employee', string='Responsible financial')
    sales_responsible_id = fields.Many2one('hr.employee', string='Responsible of sales')

