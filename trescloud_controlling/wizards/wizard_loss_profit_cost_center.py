# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
import time


class WizardLossProfitCostCenter(models.TransientModel):
    _name = 'wizard.loss.profit.cost.center'
    _description = "Wizards center cost"

    def action_export_excel(self):
        data = self.read(['report', 'date_start', 'date_end', 'detail_by_period', 'include_archived',
                          'analytic_ids'])[0]
        return self.env['report.loss.profit.cost.center'].generate_report_xls(data)

    report = fields.Selection([
        ('report_1', 'Reporte de pérdidas y ganancias')],
        string="Work Sheet")

    date_start = fields.Date(
        string='Date start',
        default=lambda *a: time.strftime('%Y-01-01'))

    date_end = fields.Date(
        string='Date end',
        default=fields.Date.today())

    detail_by_period = fields.Boolean(
        string='Detail by period')

    include_archived = fields.Boolean(
        string='Include archived')

    analytic_ids = fields.Many2many(
        'account.analytic.account',
        'wizard_report_loss_profit_cost_center_rel',
        'wizard_id',
        'analytic_id',
        string='Cost centers')
