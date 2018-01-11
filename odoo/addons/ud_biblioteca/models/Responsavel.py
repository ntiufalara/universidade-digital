# encoding: UTF-8

from odoo import models, fields, api


class Responsavel(models.Model):
    _name = 'ud.biblioteca.responsavel'

    name = fields.Char(u'Nome', compute='get_name')
    pessoa_id = fields.Many2one('res.users', u'Pessoa', required=True)
    campus_id = fields.Many2one('ud.campus', u'Campus', required=True)
    admin_campus = fields.Boolean(u'Administrador do campus')
    polo_id = fields.Many2one('ud.polo', u'Polo', required=False)

    _sql_constraints = [
        ('pessoa_id_uniq', 'unique(pessoa_id)',
         "Encontramos outro registro para a mesma pessoa, por favor edite ou apague o outro registro pra salvar.")
    ]

    @api.one
    @api.depends('campus_id', 'pessoa_id', 'polo_id')
    def get_name(self):
        polo_name = "--" if not self.polo_id.name else self.polo_id.name
        self.name = "{}; Campus: {}; Polo: {}".format(self.pessoa_id.name, self.campus_id.name, polo_name)
