# encoding: UTF-8
from odoo import models, fields


class Curso(models.Model):
    """
    Representação do Curso da Universidade.
    """
    _name = 'ud.curso'
    _inherit = 'ud.curso'

    publicacao_ids = fields.One2many('ud.biblioteca.publicacao', 'curso_id', u'Publicações')