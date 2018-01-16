# encoding: UTF-8

from odoo import models, fields


class Fabricante(models.Model):
    """
    Cadastro de fabricante
    """
    _name = 'ud.almoxarifado.fabricante'

    name = fields.Char(u'Nome', required=True)
