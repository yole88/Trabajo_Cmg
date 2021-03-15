# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class Company(models.Model):
    _inherit = 'res.company'
    
    inv_trial_balance_account_ids = fields.Many2many(
                                'account.account',
                                string=u'Balance de comprobación (Inventario)',
                                help=u'Agregar las cuentas contables que tienen relación con movimientos de inventario, '
                                u'útil para el cruce del reporte de balace de comprobación inventario.')