# encoding: UTF-8

from odoo import models, fields, api


class PessoaContato(models.Model):
    _name = 'ud.pessoa.contato'
    _description = u'Pessoa Contato'
    _order = u'tipo'

    name = fields.Char(u'Nome')
    tipo = fields.Selection([(u'telefone', u'Telefone'), (u'email', u'E-mail')], u'Tipo', required=True)
    contato = fields.Char(u'Contato', required=True)
    pessoa_id = fields.Many2one('res.users', u'Pessoa')

    @api.one
    def get_name(self):
        self.name = u'{}: {}'.format(self.tipo, self.contato)
