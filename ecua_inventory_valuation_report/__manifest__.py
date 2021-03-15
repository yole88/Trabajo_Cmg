# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Reporte de balances de comprobación de inventario',
    'version': '1.0',
    'category': 'Ecuadorian Regulations',
     'description': '''
        Reporte complementario para el cruce entre la contabilidad
        y los movimientos de inventario.
    ''',
    'website': 'http://www.trescloud.com',
    'author': 'TRESCLOUD CIA LTDA',
    'maintainer': 'TRESCLOUD CIA. LTDA.',
    'license': 'OEEL-1',
    'depends': ['base', 'account', 'ecua_kardex'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_company_view.xml',
        'wizards/inventory_balance_report_wizard.xml',
    ],
    'installable': True,
    'application': False,
}
