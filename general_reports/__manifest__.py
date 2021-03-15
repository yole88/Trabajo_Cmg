# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Reporte excel',
    'version': '1.0',
    'category': 'Sale',
     'description': '''
        Reporte excel.
    ''',
    'website': 'http://www.trescloud.com',
    'author': 'TRESCLOUD CIA LTDA',
    'maintainer': 'TRESCLOUD CIA. LTDA.',
    'license': 'OEEL-1',
    'depends': ['base'],
    'data': [
        'views/base_file_report.xml',
    ],
    'installable': True,
    'application': False,
}
