# encoding: UTF-8
from odoo import models, fields, api


class EstoqueSaida(models.Model):
    """
    Saída de estoque
    """
    _name = 'ud.almoxarifado.saida'

    name = fields.Char(u'nome', compute='get_name')
    data_saida = fields.Datetime(u'Data', required=True, default=fields.datetime.now())
    quantidade = fields.Integer(u'Quantidade', required=True)
    observacao = fields.Text(u'Observações')
    estoque_id = fields.Many2one('ud.almoxarifado.estoque', u'Estoque', invisible=True, ondelete='cascade')
    solicitacao_id = fields.Many2one('ud.almoxarifado.solicitacao', u'Solicitação')

    @api.one
    def get_name(self):
        self.name = "ALM_SAIDA_{}".format(self.id)
