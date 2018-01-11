# encoding: UTF-8

from odoo import models, fields


class OrientadorTitulacao(models.Model):
    """
    Nome: ud.biblioteca.orientador.titulacao
    Descrição: Relação Many2many de orientador para titulação, permite adicionar mais de uma titulação
    """
    _name = 'ud.biblioteca.orientador.titulacao'

    name = fields.Char(u"Nome", required=True)
    sigla = fields.Char(u'Sigla', required=True)
    orientador_ids = fields.One2many('ud.biblioteca.publicacao.orientador', 'titulacao_id', u'Orientadores')
