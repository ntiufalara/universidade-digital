# -*- coding: utf-8 -*-
{
    "name": u"Autemticação (UD)",
    "version": "2.0",
    "category": u"Universidade Digital",
    "description": u"""Configurações de autenticação da aplicação Universidade Digital.""",
    "author": "NTI UFAL Arapiraca",
    "images": [],
    "depends": ["base", "base_setup", 'ud', 'auth_signup'],
    "init_xml": [],

    "data": [
        # Segurança

        # Dados
        "data/email_template.xml",
        # Views
    ],
    "installable": True,
    "application": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
