# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


{
    "name": "Monitoria (UD)",
    "version": "1.1",
    "category": u"Universidade Digital",
    "summary": u"Gerenciamento de Monitores e Tutores",
    "licence": "AGPLv3",
    "description": u"""Módulo de Monitoria
===================
Esse módulo irá permitir a criação e gerenciamento de Processos Seletivo, suas inscrições e monitores/tutores com seus respectivos orientadores e disciplinas.""",
    "author": u"Cloves Oliveira",
    "data": [
        # Dados Iniciais
        # "data/cron.xml",
        "security/ud_monitoria_security.xml",
        "security/ir.model.access.csv",
        # Wizards
        "wizards/alteracao_bolsas_wizard_view.xml",
        "wizards/inscricao_wizard_view.xml",
        "wizards/desligamento_wizard_view.xml",
        "wizards/disciplinas_para_ps_view.xml",
        # Views
        "views/adicional_view.xml",
        "views/coordenacao_view.xml",
        "views/inscricao_view.xml",
        "views/processo_seletivo_view.xml",
        "views/orientador_view.xml",
        "views/discente_view.xml",
        "views/menus_view.xml",
    ],
    "depends": ["web_m2x_options", "ud"],
    "js": [
        "static/src/js/ud_monitoria.js",
    ],
    "qweb": [
        "static/src/xml/ud_monitoria.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
