# -*- encoding: UTF-8 -*-

{
    'name': 'Biblioteca (UD)',
    'version': '1.0',
    'category': 'Universidade Digital',
    'depends': ['base', 'ud'],
    'data': [
        'security/ud_biblioteca_security.xml',
        'security/ir.model.access.csv',
        'biblioteca_view.xml',
        'wizards/substituir_palavra_chave_wizard_view.xml',
        'wizards/substituir_orientador_wizard_view.xml',
    ],
    'css': [
        'static/src/css/*.css',
    ],
    'installable': True,
}
