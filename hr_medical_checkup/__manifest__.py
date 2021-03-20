# -*- coding: utf-8 -*-
{
    'name': "Revisiones médicas",

    'summary': """
        Revisiones médicas.
    """,

    'description': """
        Control de la revisiones médicas de los empleados.
    """,

    'author': "Digitaly Solutions",
    'category': 'Human Resources',
    'version': '1.0',
    'depends': [
                'hr'
                ],
    "data": [
        'security/ir.model.access.csv',
        'views/hr_medical_checkup.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False
}
