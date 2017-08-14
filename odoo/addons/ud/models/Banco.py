# encoding: UTF-8
from odoo import models, fields

import utils


class Banco(models.Model):
    """
    Cadastro de bancos para uso no módulo de monitoria
    """

    _name = 'ud.banco'
    _order = 'banco asc'

    name = fields.Char(u"Nome", compute='get_name')
    banco = fields.Selection(utils.BANCOS, u"Banco", required=True)
    agencia = fields.Boolean(u"Agência")
    dv_agencia = fields.Boolean(u"DV da Agência", help=u"Dígito verificador da agência")
    conta = fields.Boolean(u"Conta")
    dv_conta = fields.Boolean(u"DV da Conta", help=u"Dígito verificador da conta")
    operacao = fields.Boolean(u"Operação", help=u"Tipo de conta")

    _defaults = {
        'agencia': True,
        'conta': True,
        'dv_conta': True,
    }

    _sql_constraints = [
        ('banco_uniq', 'unique (banco)', u"Não é permitido duplicar bancos!"),
    ]

    def get_name(self):
        self.name = utils.BANCOS[self.banco]
