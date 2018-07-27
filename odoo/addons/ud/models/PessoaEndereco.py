# encoding: UTF-8

from odoo import models, fields, api
from odoo.addons.ud.models import utils


class PessoaEndereco(models.Model):
    _name = 'ud.pessoa.endereco'
    _description = u'Pessoa Endereço'

    name = fields.Char(u'Nome', compute='get_name')
    cep = fields.Char(u'CEP')
    rua = fields.Char(u'Rua/Logradouro', required=True)
    complemento = fields.Char(u'Complemento')
    numero = fields.Char(u"Número", required=True)
    bairro = fields.Char(u'Bairro', required=True)
    cidade = fields.Char(u'Cidade', required=True)
    estado = fields.Selection(utils.ESTADOS, u'Estado', required=True)
    pais = fields.Char(u'País', required=True, default=u'Brasil')
    pessoa_id = fields.Many2one('res.users', u'Pessoa')

    @api.one
    def get_name(self):
        self.name = u'{}; {}; {}'.format(self.rua, self.bairro, self.cidade)


