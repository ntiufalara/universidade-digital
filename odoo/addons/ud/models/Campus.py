# encoding: UTF-8
from odoo import models, fields


class Campus(models.Model):
    _name = 'ud.campus'

    name = fields.Char(u'Nome', size=40, required=True, help=u"Ex.: Arapiraca, Sertão, Litoral etc.")
    diretor = fields.Many2one('res.users', u'Diretor', )
    diretor_academico = fields.Many2one('res.users', u'Diretor Acadêmico',)

