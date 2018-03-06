# encoding: UTF-8

{
    "name": u"Rserva de espaço UD",
    "version": "2.0",
    "category": u"Universidade Digital",
    "description": u"""Repositório institucional controlado pela biblioteca do campus.""",
    "author": "NTI UFAL Arapiraca",
    "depends": ["ud"],
    "data": [
        # Segurança
        "security/ud_reserva_security.xml",
        "security/ir.model.access.csv",
        # Views
        "views/backend/assets.xml",
        "views/reserva_view.xml",
        "views/reserva_dia_view.xml",
        "views/responsavel_view.xml",
        "views/menus.xml",
        "wizards/adicionar_dias_wizard_view.xml",
        "wizards/cancelamento_reserva_wizard.xml",
        # Dados
        "data/load_reserva_openerp7_cron.xml",
    ],
    "installable": True,
    "application": True,
}
