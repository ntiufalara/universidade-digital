# encoding: UTF-8

from odoo import models, fields, api


class AlmoxarifadoResponsavel(models.Model):
    """
    Responsável por cada um dos almoxarifados cadastrados
    """
    _name = 'ud.almoxarifado.responsavel'

    name = fields.Char(u'Nome', compute='get_name')
    pessoa_id = fields.Many2one('res.users', u'Pessoa')
    almoxarifado_ids = fields.Many2many('ud.almoxarifado.almoxarifado', 'almoxarifado_responsavel_rel',
                                        string=u'Almoxarifados')

    @api.one
    def get_name(self):
        self.name = self.pessoa_id.name
