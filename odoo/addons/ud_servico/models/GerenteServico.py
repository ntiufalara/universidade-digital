# encoding: UTF-8

from odoo import models, fields, api


class GerenteServico(models.Model):
    """
    Ao criar este registro, adiciona o gerente ao grupo de permissões atribui um local ao gerente
    """
    _name = 'ud.servico.gerente'

    name = fields.Char(u'Nome', compute='get_name')
    pessoa_id = fields.Many2one('res.users', u'Pessoa', required=True, default=lambda self: self.get_pessoa())
    campus_id = fields.Many2one('ud.campus', u'Campus', required=True)
    polo_id = fields.Many2one('ud.polo', u'Polo')

    @api.one
    def get_name(self):
        self.name = self.pessoa_id.name

    def get_pessoa(self):
        if self.env.context.get('active_model') == 'res.users':
            return self.env.context.get('active_id')
        return False

    @api.model
    def create(self, vals):
        res = super(GerenteServico, self).create(vals)
        group_gerente_servico = self.env.ref('base.gerente_os')
        res.pessoa_id.groups_id |= group_gerente_servico
        return res
