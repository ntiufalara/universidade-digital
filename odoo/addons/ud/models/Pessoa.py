# encoding: UTF-8
from odoo import models, fields, api
import utils
import logging

_logger = logging.getLogger(__name__)

# http://www.odoo.com/documentation/10.0/reference/mixins.html


class Pessoa(models.Model):
    """
    Classe que representa os campos do formulário Pessoa.
    """
    _name = 'res.users'
    _inherit = 'res.users'

    name = fields.Char(u'Nome completo', required=True)
    cpf = fields.Char(u'CPF', help=u"Entre o CPF no formato: XXX.XXX.XXX-XX")
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
    telefone_fixo = fields.Char(u'Telefone principal')
    celular = fields.Char(u'Celular')
    email = fields.Char(u'E-mail')
    orgaoexpedidor = fields.Char(u'Orgão Expedidor', size=10, help=u"Sigla: Ex. SSP/SP")

    dados = fields.One2many('ud.dados.bancarios', 'pessoa_id', u'Dados Bancários')
    nacionalidade = fields.Selection(utils.NACIONALIDADES, u'Nacionalidade', default='br')
    rua = fields.Char(u'Rua')
    numero = fields.Char(u"Número")
    bairro = fields.Char(u'Bairro')
    cidade = fields.Char(u'Cidade')
    estado = fields.Selection(utils.ESTADOS, u'Estado')
    curriculo_lattes_link = fields.Char(u'Link do Currículo Lattes')
    perfil_ids = fields.One2many('ud.perfil', 'pessoa_id', u'Perfil')

    _sql_constraints = [
        ("ud_cpf_uniq", "unique(cpf)", u'Já existe CPF com esse número cadastrado.'),
        ("ud_rg_uniq", "unique(rg)", u'Já existe RG com esse número cadastrado.'),
    ]

    @api.model
    def create(self, vals):
        """
        Detemina o login igual ao e-mail
        Adiciona o usuário no grupo "base.usuario_ud"
        :param vals:
        :return:
        """
        if vals.get('email'):
            vals['login'] = vals['email']
        obj_set = super(models.Model, self).create(vals)
        usuario_ud_group = self.env.ref('base.usuario_ud')
        obj_set.groups_id |= usuario_ud_group
        return obj_set

    def write(self, vals):
        """
        Caso o e-mail seja alterado, altera também o login
        :param vals:
        :return:
        """
        if vals and type(vals) == dict and vals.get('email'):
            vals['login'] = vals['email']
        return super(Pessoa, self).write(vals)

