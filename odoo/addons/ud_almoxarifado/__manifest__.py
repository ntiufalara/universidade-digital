# encoding: UTF-8

{
    "name": u"Almoxarifado UD",
    "version": "2.0",
    "category": u"Universidade Digital",
    "description": u"""Repositório institucional controlado pela biblioteca do campus.""",
    "author": "NTI UFAL Arapiraca",
    "depends": ["ud"],
    "data": [
        # Segurança
        "security/ud_almoxarifado_security.xml",
        "security/ir.model.access.csv",
        # Views
        "views/almoxarifado_view.xml",
        "views/fornecedor_view.xml",
        "views/estoque_view.xml",
        "views/produto_view.xml",
        "views/estoque_entrada_view.xml",
        'views/estoque_entrada_graph_view.xml',
        "views/estoque_saida_view.xml",
        'views/estoque_saida_graph_view.xml',
        "views/fabricante_view.xml",
        "views/produto_categoria_view.xml",
        "views/solicitacao_produto_view.xml",
        "views/produto_quantidade_view.xml",
        "views/responsavel_view.xml",
        "views/remessa_entrada_view.xml",
        "views/remessa_saida_view.xml",
        "views/menus.xml",
        # Dados
        # "data/ud_biblioteca_publicacao_tipo_data.xml",
    ],
    "installable": True,
    "application": True,
}
