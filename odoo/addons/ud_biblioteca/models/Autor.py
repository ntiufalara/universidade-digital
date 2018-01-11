# encoding: UTF-8

from odoo import models, fields


class Autor(models.Model):
    """
    Nome: ud.biblioteca.publicacao.autor
    Descrição: Cadastro de autor de publicações
    """
    _name = 'ud.biblioteca.publicacao.autor'

    name = fields.Char(u'Nome', required=True)
    contato = fields.Char(u'E-mail')
