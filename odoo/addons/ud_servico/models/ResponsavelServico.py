# encoding: UTF-8

from odoo import models, fields, api
from odoo.addons.ud_servico.models import utils


class ResponsavelAnaliseServico(models.Model):
    """
    Responsável por analisar e encaminhar uma OS para execução
    """
    _name = 'ud.servico.responsavel'

    name = fields.Char('Nome', compute='get_name')
    responsavel_id = fields.Many2one('res.users', u'Responsável', required=True)
    tipo = fields.Selection(utils.TIPO_RESPONSAVEL, u'Tipo', required=True)

    @api.one
    def get_name(self):
        self.name = self.responsavel_id.name
