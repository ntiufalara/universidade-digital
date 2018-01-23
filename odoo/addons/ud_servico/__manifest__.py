# encoding: UTF-8

{
    "name": u"Ordem de Serviço UD",
    "version": "2.0",
    "category": u"Universidade Digital",
    "description": u"""Gerenciamento de solicitações de serviço e ordens de serviço""",
    "author": "NTI UFAL Arapiraca",
    "depends": ["ud"],
    "data": [
        # Segurança
        "security/ud_servico_security.xml",
        # "security/ir.model.access.csv",
        # Views
        # "views/backend/assets.xml",
        # "views/reserva_view.xml",
        # "views/reserva_dia_view.xml",
        # "views/responsavel_view.xml",
        # "views/menus.xml",
        # "wizards/adicionar_dias_wizard_view.xml",
        # "wizards/cancelamento_reserva_wizard.xml",
        # Dados
        "data/tipo_manutencao_data.xml",
        "data/tipo_equipamento_data.xml",
        "data/tipo_equipamento_eletrico_data.xml",
        "data/tipo_ar_condicionado_data.xml",
        "data/tipo_predial_data.xml",
        "data/tipo_instalacoes_data.xml",
    ],
    "installable": True,
    "application": True,
}
