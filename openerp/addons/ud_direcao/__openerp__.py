# -*- coding: utf-8 -*-
{
    'name': 'Repositório de portarias (UD)',
    'version': '1.0',
    'category': 'college',
    'description': """
Repositório de portarias da aplicação Universidade Digital.
    """,
    'author': 'NTI UFAL Arapiraca',
    'images': [],
    'depends': ['ud'],
    'init_xml': [],

    'data': [
        'security/ud_direcao_security.xml',
        'security/ir.model.access.csv',
        'views/portaria_view.xml',
        'views/setor_view.xml',
        'views/menus.xml',
    ],
    "js": [

    ],
    'installable': True,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
