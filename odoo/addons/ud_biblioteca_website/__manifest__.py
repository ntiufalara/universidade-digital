# -*- coding: utf-8 -*-


{
    "name": "Site Biblioteca",
    "summary": "Complemento para ud_website: Exibe o respositório no site principal",
    "version": "10.0.1.0.18",
    "category": "Site UD",
    "website": "http://ud.arapiraca.ufal.br",
    "description": """""",
    "author": "NTI UFAL Arapiraca",
    "license": "MIT",
    "installable": True,
    "depends": ['ud_website', 'ud_biblioteca'],
    "data": [
        # security
        'security/ir.model.access.csv',
        # 'views/assets.xml',
        'views/home.xml',
        'views/home_repositorio.xml',
        'views/publicacoes.xml',
    ],
}
