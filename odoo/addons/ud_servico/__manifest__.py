# encoding: UTF-8

{
    "name": u"Ordem de Serviço UD",
    "version": "2.0",
    "category": u"Universidade Digital",
    "description": u"""Gerenciamento de solicitações de serviço e ordens de serviço""",
    "author": "NTI UFAL Arapiraca",
    "depends": ["ud", 'mail'],
    "data": [
        # Dados
        "data/tipo_manutencao_data.xml",
        "data/tipo_equipamento_data.xml",
        "data/tipo_equipamento_eletrico_data.xml",
        "data/tipo_refrigerador_data.xml",
        "data/tipo_ar_condicionado_data.xml",
        "data/tipo_predial_data.xml",
        "data/tipo_instalacoes_data.xml",
        # Segurança
        "security/ud_servico_security.xml",
        "security/ir.model.access.csv",
        # Views
        "views/solicitacao_servico_view.xml",
        "views/responsavel_servico_view.xml",
        "views/menus.xml",
        # Wizards Views
        "wizards/para_analise_wiz/atribuir_responsavel_wiz_view.xml",
        "wizards/para_execucao_wiz/atribuir_previsao_wiz_view.xml",
        "wizards/executar_wiz/atribuir_execucao_view.xml",
        "wizards/finalizar_wiz/finalizar_servico_view.xml",
        "wizards/cancelar_wiz/cancelar_servico_view.xml",
        # "wizards/adicionar_dias_wizard_view.xml",
        # "wizards/cancelamento_reserva_wizard.xml",
    ],
    "installable": True,
    "application": True,
}
