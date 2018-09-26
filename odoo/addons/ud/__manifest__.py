# -*- coding: utf-8 -*-
{
    "name": u"Universidade Digital",
    "version": "2.0",
    "category": u"Universidade Digital",
    "description": u"""Núcleo da aplicação Universidade Digital.""",
    "author": "NTI UFAL Arapiraca",
    "images": [],
    "depends": ['inputmask_widget', 'auth_signup'],
    "init_xml": [],
    "data": [
        # Segurança
        'security/ud_security.xml',
        'security/ir.model.access.csv',
        # Dados
        'data/ud_perfil_tipo_data.xml',
        'data/ud_perfil_tipo_docente_data.xml',
        'data/ud_curso_modalidade_data.xml',
        # Cron job
        'data/load_openerp7_cron.xml',
        # Views
        'views/pessoa_view.xml',
        'views/campus_view.xml',
        'views/polo_view.xml',
        'views/setor_view.xml',
        'views/disciplina_view.xml',
        'views/curso_view.xml',
        'views/espaco_view.xml',
        'views/perfil_view.xml',
        'views/server_openerp7_view.xml',
        'views/pessoa_contato_view.xml',
        'views/pessoa_endereco_view.xml',
        'views/bloco_view.xml',
        'views/menus.xml',
    ],
    "installable": True,
    "application": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
