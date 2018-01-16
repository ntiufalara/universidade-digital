# encoding: UTF-8

from odoo import models, fields


class EstoqueSaida(models.Model):
    """
    Saída de estoque
    """
    _name = 'ud.almoxarifado.saida'

    data_saida = fields.Datetime(u'Data de saída', required=True)
    quantidade = fields.Integer(u'Quantidade', required=True)
    observacao = fields.Text(u'Observação')
    estoque_id = fields.Many2one('ud.almoxarifado.estoque', u'Estoque', invisible=True, ondelete='cascade')
