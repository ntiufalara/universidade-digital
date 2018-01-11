# encoding: UTF-8

from odoo import models, fields


class Bolsa(models.Model):
    _name = 'ud.bolsa'

    sigla = fields.Char(u'Sigla', required=True)
    name = fields.Char(u'Nome', required=True)
    valor = fields.Float(u'Valor')
