# -*- coding: utf-8 -*-
# Copyright 2016 Openworx, LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    "name": "Tema Universidade Digital",
    "summary": "Tema da aplicação Universidade Digital baseado no LasLabs web_responsive",
    "version": "10.0.1.0.18",
    "category": "Themes/Backend",
    "website": "http://ud.arapiraca.ufal.br",
    "description": """
		Backend theme for Odoo 10.0 community edition.
		The app dashboard is based on the module web_responsive from LasLabs Inc and the theme on Bootstrap United.
    """,
    'images': [
        'images/screen.png'
    ],
    "author": "NTI UFAL Arapiraca",
    "license": "LGPL-3",
    "installable": True,
    "depends": [
        'web',
    ],
    "data": [
        'views/assets.xml',
        'views/web.xml',
        # 'views/ud_layout.xml',
    ],
}
