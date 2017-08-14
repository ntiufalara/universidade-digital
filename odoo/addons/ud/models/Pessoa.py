# encoding: UTF-8
from odoo import models, fields, api
import utils


class Pessoa(models.Model):
    """
    Classe que representa os campos do formulário Pessoa.
    """
    _name = 'res.users'
    _inherit = 'res.users'

    name = fields.Char(u'Nome completo', required=True)
    cpf = fields.Char(u'CPF', help=u"Entre o CPF no formato: XXX.XXX.XXX-XX", required=True)
    rg = fields.Char(u'RG', size=20)
    data_nascimento = fields.Date(u'Data de nascimento')
    genero = fields.Selection(
        [('masculino', u'Masculino'),
         ('feminino', u'Feminino')], u'Gênero'
    )
    estado_civil = fields.Selection(
        [('solteiro', u'Solteiro'), ('casado', u'Casado'), ('viuvo', u'Viúvo'), ('divorciado', u'Divorciado')],
        u'Estado Civil', default='solteiro'
    )
    telefone_fixo = fields.Char(u'Telefone fixo')
    celular = fields.Char(u'Celular')
    email = fields.Char(u'E-mail')
    orgaoexpedidor = fields.Char(u'Orgão Expedidor', size=8, help=u"Sigla: Ex. SSP/SP")

    dados = fields.One2many('ud.dados.bancarios', 'pessoa_id', u'Dados Bancários')
    nacionalidade = fields.Selection(utils.NACIONALIDADES, u'Nacionalidade', default='br')
    rua = fields.Char(u'Rua', size=120)
    numero = fields.Char(u"Número", size=8)
    bairro = fields.Char(u'Bairro', size=32)
    cidade = fields.Char(u'Cidade', size=120)
    estado = fields.Selection(utils.ESTADOS, u'Estado')
    curriculo_lattes_link = fields.Char(u'Link do Currículo Lattes')
    # user_id = fields.Many2one('res.users', 'Usuário', required=True, ondelete='cascade')

    _sql_constraints = [
        ("ud_cpf_uniq", "unique(cpf)", u'Já existe CPF com esse número cadastrado.'),
        ("ud_rg_uniq", "unique(rg)", u'Já existe RG com esse número cadastrado.'),
    ]

    @api.model
    def create(self, vals):
        vals['login'] = vals['cpf']
        return super(models.Model, self).create(vals)

    def write(self, vals):
        if vals and type(vals) == dict and vals.get('cpf'):
            vals['login'] = vals['cpf']
        return super(Pessoa, self).write(vals)
