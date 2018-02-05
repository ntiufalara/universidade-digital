# encoding: UTF-8

from odoo import models, fields, api


class GerenteServico(models.Model):
    """
    Ao criar este registro, adiciona o gerente ao grupo de permissões atribui um local ao gerente
    """
    _name = 'ud.servico.gerente'

    name = fields.Char(u'Nome', compute='get_name')
    pessoa_id = fields.Many2one('res.user', u'Pessoa', required=True)
    campus_id = fields.Many2one('ud.campus', u'Campus', required=True)
    polo_id = fields.Many2one('ud.polo', u'Polo')

    @api.one
    def get_name(self):
        self.name = self.pessoa_id.name

    @api.model
    def create(self, vals):
        res = super(GerenteServico, self).create(vals)
        group_gerente_servico = self.env.ref('base.gerente_os')
        res.pessoa_id.groups_id |= group_gerente_servico
        return res
