# -*- coding: utf-8 -*-
{
    'name': "Ficha de empleados",

    'summary': """
        Ficha de empleados.
    """,

    'description': """
         Ficha de empleados.
    """,

    'author': "Digitaly Solutions",
    'category': 'Human Resources',
    'version': '1.0',
    'depends': [
                'hr'
                ],
    "data": [
        'views/hr_employee_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False
}
