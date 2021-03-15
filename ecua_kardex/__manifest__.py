# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Reportes de Valorización de Inventario',
    'version': '1.0',
    'category': 'Ecuadorian Regulations',
     'description': '''
       
    ''',
    'website': 'http://www.trescloud.com',
    'author': 'TRESCLOUD CIA LTDA',
    'maintainer': 'TRESCLOUD CIA. LTDA.',
    'license': 'OEEL-1',
    'depends': ['base', 'account', 'general_reports'],
    'data': [
        'security/ir.model.access.csv',
        'wizards/wizard_stock_history.xml',
    ],
    'installable': True,
    'application': False,
}
