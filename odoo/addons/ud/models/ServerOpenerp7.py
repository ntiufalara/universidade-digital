# encoding: UTF-8
from odoo import models, fields


class ServerOpenerp7(models.Model):
    """
    Representação do Polo (local)
    """
    _name = 'ud.server.openerp7'

    name = fields.Char(u'Nome', required=True, help=u"Ex: UD openerp 7")
    url = fields.Char(u'URL', required=True)
    db = fields.Char(u'Banco de dados', required=True)
    username = fields.Char(u'Nome de usuário', required=True)
    password = fields.Char(u'Senha', required=True)


