# encoding: UTF-8

from odoo import models, fields


class Anexo(models.Model):
    """
    Nome: ud.biblioteca.anexo
    Deescrição: Arquivos contendo as publicações
    """
    _name = 'ud.biblioteca.anexo'

    name = fields.Char(u'Anexo', required=True)
    arquivo = fields.Binary(u'Arquivo PDF', filter='*.pdf')
    publicacao_id = fields.Many2one('ud.biblioteca.publicacao', u'Publicação')

