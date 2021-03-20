# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Reportes contables adicionales',
    'version': '1.0',
    'category': 'Account',
     'description': '''
        Funcionalidad:
        Este modulo agrega los siguientes reportes:
        1- Reporte de pérdidas y ganancias
    ''',
    'website': 'http://www.trescloud.com',
    'author': 'TRESCLOUD CIA LTDA',
    'maintainer': 'TRESCLOUD CIA. LTDA.',
    'license': 'OEEL-1',
    'depends': ['base', 'analytic', 'general_reports'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_analytic_account.xml',
        'wizards/wizard_loss_profit_cost_center.xml',
    ],
    'installable': True,
    'application': False,
}
