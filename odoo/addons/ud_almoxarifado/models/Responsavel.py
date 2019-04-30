# encoding: UTF-8
from odoo import models, fields, api


class Responsavel(models.Model):
    _name = 'ud.almoxarifado.responsavel'

    name = fields.Char(u'Nome', compute='get_name')
    pessoa_id = fields.Many2one('res.users', u'Pessoa', required=True)
    campus_id = fields.Many2one('ud.campus', u'Campus', required=True)
    polo_id = fields.Many2one('ud.polo', u'Polo', required=False)
    almoxarifado_ids = fields.Many2many('ud.almoxarifado.almoxarifado', 'ud_almoxarifado_responsavel_rel',
                                        string=u'Almoxarifados', required=True)

    _sql_constraints = [
        ('pessoa_id_uniq', 'unique(pessoa_id)',
         "Encontramos outro cadastro para a mesma pessoa, por favor edite ou apague o outro registro pra salvar.")
    ]

    @api.one
    @api.depends('campus_id', 'pessoa_id', 'polo_id')
    def get_name(self):
        polo_name = "--" if not self.polo_id.name else self.polo_id.name
        self.name = u"{}; Campus: {}; Polo: {}".format(self.pessoa_id.name, self.campus_id.name, polo_name)

    @api.model
    def create(self, vals):
        res = super(Responsavel, self).create(vals)
        group_gerente_servico = self.env.ref('ud_almoxarifado.group_ud_almoxarifado_gerente')
        res.pessoa_id.groups_id |= group_gerente_servico
        return res
