# encoding: UTF-8
from odoo import models, fields


class Setor(models.Model):
    """
    Representação do Setor da Universidade
    """
    _name = 'ud.setor'

    name = fields.Char(u'Nome', size=80, required=True)
    descricao = fields.Text(u'Descrição')
    polo_id = fields.Many2one('ud.polo', u'Polo', required=True, ondelete='cascade')
    sigla = fields.Char(u'Sigla', size=50, required=True)
    is_active = fields.Boolean(u'Ativo?', default=True)
