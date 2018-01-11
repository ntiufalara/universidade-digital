# encoding: UTF-8

from odoo import models, fields, api


class Orientador(models.Model):
    """
    Nome: ud.biblioteca.orientador
    Deescrição: Relação many2many de publicação para orientador, permite adicionar mais de um orientador
    """
    _name = 'ud.biblioteca.publicacao.orientador'

    # Nome de exibição
    name = fields.Char(u'Nome', compute='get_name')
    # Nome preenchido pelo usuário
    nome_orientador = fields.Char(u'Nome completo', required=True)
    titulacao_id = fields.Many2one('ud.biblioteca.orientador.titulacao', u'Titulação')
    publicacao_orientador_ids = fields.Many2many('ud.biblioteca.publicacao', 'publicacao_orientador_rel',
                                                 string=u'Orientador em')
    publicacao_coorientador_ids = fields.Many2many('ud.biblioteca.publicacao', 'publicacao_coorientador_rel',
                                                   string=u'Coorientador em')

    @api.depends('nome_orientador', 'titulacao_id')
    @api.one
    def get_name(self):
        self.name = u"{} {}".format(self.titulacao_id.sigla, self.nome_orientador) if self.titulacao_id else self.nome_orientador
