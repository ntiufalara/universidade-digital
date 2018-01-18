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
        # "security/ud_biblioteca_security.xml",
        # "security/ir.model.access.csv",
        # Views
        "views/almoxarifado_view.xml",
        "views/fornecedor_view.xml",
        "views/estoque_view.xml",
        "views/menus.xml",
        # Dados
        # "data/ud_biblioteca_publicacao_tipo_data.xml",
    ],
    "installable": True,
    "application": True,
}
