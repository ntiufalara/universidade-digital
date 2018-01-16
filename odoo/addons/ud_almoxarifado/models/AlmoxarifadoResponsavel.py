# encoding: UTF-8

from odoo import models, fields, api


class AlmoxarifadoResponsavel(models.Model):
    """
    Responsável por cada um dos almoxarifados cadastrados
    """
    _name = 'ud.almoxarifado.almoxarifado.responsavel'

    name = fields.Char(u'Nome', compute='get_name')
    pessoa_id = fields.Many2one('res.users', u'Pessoa')

    @api.one
    def get_name(self):
        self.name = self.pessoa_id.name
