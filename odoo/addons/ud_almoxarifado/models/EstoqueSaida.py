# encoding: UTF-8
from odoo import models, fields, api


class EstoqueSaida(models.Model):
    """
    Saída de estoque
    """
    _name = 'ud.almoxarifado.saida'

    name = fields.Char(u'nome', compute='get_name')
    data_saida = fields.Datetime(u'Data de saída', required=True, default=fields.datetime.now())
    quantidade = fields.Integer(u'Quantidade', required=True)
    observacao = fields.Text(u'Observação')
    estoque_id = fields.Many2one('ud.almoxarifado.estoque', u'Estoque', invisible=True, ondelete='cascade')

    @api.one
    def get_name(self):
        self.name = "Data: {}; Quantidade: {}; Produto: {}".format(self.data_saida.strftime('%d/%m/%Y'),
                                                                   self.quantidade, self.estoque_id.name)
