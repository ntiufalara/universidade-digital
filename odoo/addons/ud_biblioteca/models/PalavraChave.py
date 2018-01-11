# encoding: UTF-8

from odoo import models, fields


class PalavraChave(models.Model):
    """
    Nome: ud.biblioteca.p_chave
    Descrição: Armazenar as palavras-chave de cada publicação
    """
    _name = 'ud.biblioteca.p_chave'

    name = fields.Char('Palavra-chave', required=True)
    publicacao_id = fields.Many2many('ud.biblioteca.publicacao', 'publicacao_p_chave_rel', string=u'Palavras-chave',
                                     ondelete='set null')
