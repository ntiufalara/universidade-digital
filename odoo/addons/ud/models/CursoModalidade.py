# encoding: UTF-8

from odoo import models, fields


class CursoModalidade(models.Model):
    _name = 'ud.curso.modalidade'

    name = fields.Char(u'Nome', required=True)
