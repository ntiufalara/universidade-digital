# encoding: UTF-8

{
    "name": u"Repositório de portarias (UD)",
    "version": "2.0",
    "category": u"Universidade Digital",
    "description": u"""Repositório de portarias da aplicação Universidade Digital.""",
    "author": "NTI UFAL Arapiraca",
    "depends": ["ud"],
    "data": [
        # Segurança
        "security/ud_direcao_security.xml",
        "security/ir.model.access.csv",
        # Views
        "views/setor_view.xml",
        "views/portaria_view.xml",
        "views/menus.xml",
        # Dados
        "data/load_portarias_openerp7_cron.xml",
    ],
    "installable": True,
    "application": True,
}
