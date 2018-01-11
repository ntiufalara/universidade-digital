# encoding: UTF-8

from odoo import models, fields


class CategoriaCnpq(models.Model):
    """
    Nome: ud.biblioteca.publicacao.categoria_cnpq
    Descrição: Cadastro de Categorias CNPQ
    """
    _name = 'ud.biblioteca.publicacao.categoria_cnpq'

    name = fields.Char(u'Nome', required=True)
    publicacao_ids = fields.Many2many('ud.biblioteca.publicacao', 'categoria_cnpq_ids', string=u'Publicações')
