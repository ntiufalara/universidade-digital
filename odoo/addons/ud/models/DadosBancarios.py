# encoding: UTF-8
from odoo import models, fields


class DadosBancarios(models.Model):
    """
    Cadastro de dados bancários para uso no módulo de monitoria
    """
    _name = "ud.dados.bancarios"

    _rec_name = "banco_id"

    banco_id = fields.Many2one("ud.banco", u"Banco", required=True, ondelete="restrict")
    agencia = fields.Char(u"Agência", size=5, help=u"Número da Agência")
    dv_agencia = fields.Char(u"DV Agência", size=4, help=u"Dígito verificador da Agência")
    conta = fields.Char(u"Conta", size=10, help=u"Número da Conta")
    dv_conta = fields.Char(u"DV Conta", size=4, help=u"Dígito verificador da Conta")
    operacao = fields.Char(u"Operação", size=4, help=u"Tipo de conta")
    pessoa_id = fields.Many2one("res.users", u"Proprietário", invisible=True, ondelete="cascade")
