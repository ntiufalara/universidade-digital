# encoding: UTF-8

from odoo import models, fields


class TipoPublicacao(models.Model):
    """
    Nome: ud.biblioteca.publicacao.tipo
    Descrição: Cadastro de tipos de publicações
    """
    _name = 'ud.biblioteca.publicacao.tipo'
    _description = 'Tipo de publicação'

    name = fields.Char(u'Tipo', required=True)
