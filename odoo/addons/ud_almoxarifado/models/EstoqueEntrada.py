# encoding: UTF-8

from odoo import models, fields


class EstoqueEntrada(models.Model):
    """
    Entrada de estoque
    """
    _name = 'ud.almoxarifado.entrada'

    name = fields.Char(u'Nome')
    data_entrada = fields.Datetime(u'Data de entrada', required=True)
    quantidade = fields.Integer(u'Quantidade', required=True)
    tipo = fields.Selection([
        ("fornecedor", u"Fornecedor"),
        ("estorno", u"Estorno"),
        ("devolucao", u"Devolução")
    ], u"Tipo", default='fornecedor')
    estoque_id = fields.Many2one('ud.almoxarifado.estoque', u'Estoque', invisible=True, ondelete='cascade')
