# encoding: UTF-8
from odoo import models, fields


class Polo(models.Model):
    """
    Representação do Polo (local)
    """
    _name = 'ud.polo'

    name = fields.Char(u'Nome', required=True, help=u"Ex.: Viçosa, Penedo, Palmeira etc.")
    campus_id = fields.Many2one('ud.campus', u'Campus', required=True)
    localizacao = fields.Char(u'Endereço', size=120)
    is_active = fields.Boolean(u'Ativo?', default=True)
    descricao = fields.Text(u'Descrição')
    bloco_ids = fields.One2many('ud.bloco', 'polo_id', u'Bloco')

