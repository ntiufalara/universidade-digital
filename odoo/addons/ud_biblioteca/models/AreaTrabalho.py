# encoding: UTF-8

from odoo import models, fields


class AreaTrabalho(models.Model):
    """
    Nome: ud.biblioteca.publicacao.area
    Descrição: Cadastro de área de trabalho
    """
    _name = 'ud.biblioteca.publicacao.area'

    name = fields.Char(u'Área', required=True)
    publicacao_ids = fields.Many2many('ud.biblioteca.publicacao', 'area_publicacao_real', string=u'Publicações')
