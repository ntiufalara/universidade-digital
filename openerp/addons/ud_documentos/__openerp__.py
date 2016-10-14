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
    "name": u"Módulo de Documentos (UD)",
    "version": "1.1",
    "category": u"Documentos",
    "description": u"""Módulo de Documentos
====================
Permite a criação de documentos personalizáveis além de dar acesso à setores específicos.

Obs.: Ainda não oferece suporte para envio de E-mails.

Instalação do WeasyPrint:
-------------------------
* sudo apt-get install python-dev build-essential
* sudo apt-get install python-pip python-lxml libcairo2 libpango1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
* sudo pip install cffi lxml html5lib cairocffi tinycss cssselect cairosvg
* sudo pip install WeasyPrint

Se necessário, instale: sudo apt-get install python-setuptools

Maiores informações, acesse: http://weasyprint.org/docs/install/""",
    "author": u"Cloves Oliveira",
    "data": ["security/ud_documentos_security.xml",
             "security/ir.model.access.csv",
             "ud_documentos_view.xml",
             ],
    "depends": ["base", "ud"],

    "installable": True,
    "auto_install": False,
#     "application": True,
    "css": ["static/src/css/documentos.css"],
    "js": [],
    "qweb": [],
    "update_xml":[],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
