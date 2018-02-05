# encoding: UTF-8

from odoo import models, fields, api
from odoo.addons.ud_servico.models import utils


class ResponsavelAnaliseServico(models.Model):
    """
    Responsável por analisar e encaminhar uma OS para execução
    """
    _name = 'ud.servico.responsavel'

    _order = 'name asc'

    name = fields.Char('Nome', compute='get_name')
    responsavel_id = fields.Many2one('res.users', u'Responsável', required=True)
    tipo = fields.Selection(utils.TIPO_RESPONSAVEL, u'Tipo', required=True)
    solicitacao_id = fields.Many2one('ud.servico.solicitacao', u'Solicitação', ondelete='restrict')

    _sql_constraints = [
        ('responsavel_id_unique', 'unique(responsavel_id)',
         u'Este responsável já está cadastrado, use a lista para alterar o registro.')
    ]

    @api.one
    def get_name(self):
        self.name = self.responsavel_id.name

    @api.model
    def create(self, vals):
        res = super(ResponsavelAnaliseServico, self).create(vals)
        group_responsavel_servico = self.env.ref('base.responsavel_os')
        res.responsavel_id.groups_id |= group_responsavel_servico
        return res
