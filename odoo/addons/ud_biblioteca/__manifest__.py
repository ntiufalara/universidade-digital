# encoding: UTF-8

{
    "name": u"Biblioteca UD (Repositório Institucuonal)",
    "version": "2.0",
    "category": u"Universidade Digital",
    "description": u"""Repositório institucional controlado pela biblioteca do campus.""",
    "author": "NTI UFAL Arapiraca",
    "depends": ["ud"],
    "data": [
        # Segurança
        "security/ud_biblioteca_security.xml",
        "security/ir.model.access.csv",
        # Views
        "views/publicacao_view.xml",
        "views/responsavel_view.xml",
        "views/anexo_view.xml",
        "views/orientador_view.xml",
        "views/orientador_titulacao_view.xml",
        "views/p_chave_view.xml",
        "views/publicacao_tipo_view.xml",
        "views/publicacao_area_view.xml",
        "views/publicacao_autor_view.xml",
        "views/publicacao_categoria_cnpq.xml",
        'views/pessoa_override_view.xml',
        "wizards/substituir_orientador_view.xml",
        "wizards/substituir_p_chave_view.xml",
        'wizards/corrigir_titulacao_orientador.xml',
        'wizards/atualizar_titulacao_orientador.xml',
        "views/menus.xml",
        # Dados
        "data/ud_biblioteca_publicacao_tipo_data.xml",
        'data/load_publicacao_openerp7_cron.xml',
    ],
    "installable": True,
    "application": True,
}
