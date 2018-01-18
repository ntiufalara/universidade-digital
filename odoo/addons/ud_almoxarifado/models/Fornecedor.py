# encoding: UTF-8

from odoo import models, fields, api
from odoo.addons.ud.models import utils as ud_utils
from odoo.exceptions import ValidationError


class Fornecedor(models.Model):
    """
    Cadastro de Fornecedor
    """
    _name = 'ud.almoxarifado.fornecedor'
    _order = 'name asc'

    name = fields.Char(u'Fornecedor', required=True)
    cpf_cnpj = fields.Char(u'CPF/CNPJ')
    telefone_fixo = fields.Char(u'Telefone fixo')
    celular = fields.Char(u'Celular')
    email = fields.Char(u'E-mail')
    estado = fields.Selection(ud_utils.ESTADOS, u'Estado')
    cidade = fields.Char(u'Cidade')
    bairro = fields.Char(u'Bairro')
    rua = fields.Char(u'Rua')
    numero = fields.Char(u'Número')
    cep = fields.Char(u'CEP')

    _sql_constraints = [('unique_name', 'unique(name)', u"Fornecedor já cadastrado!")]

    @api.constrains('cpf_cnpj')
    def valida_cpf_cnpj(self):
        """
        Valida o formato e os digitos do CPF/CNPJ
        :return: None
        """
        if self.cpf_cnpj and not ud_utils.validar_cpf_cnpj(self.cpf_cnpj):
            raise ValidationError('CPF/CNPJ Inválido')

    @api.model
    def create(self, vals):
        """
        Converte o nome do fornecedor para Caixa alta
        :param vals:
        :return: RecordSet()
        """
        vals['name'] = vals['name'].upper()
        return super(Fornecedor, self).create(vals)
