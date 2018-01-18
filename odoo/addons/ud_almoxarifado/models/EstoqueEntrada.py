# encoding: UTF-8

from odoo import models, fields, api


class EstoqueEntrada(models.Model):
    """
    Entrada de estoque
    """
    _name = 'ud.almoxarifado.entrada'

    name = fields.Char(u'Nome', compute='get_name')
    data_entrada = fields.Datetime(u'Data', required=True, default=fields.datetime.now())
    quantidade = fields.Integer(u'Quantidade', required=True)
    tipo = fields.Selection([
        ("fornecedor", u"Fornecedor"),
        ("estorno", u"Estorno"),
        ("devolucao", u"Devolução")
    ], u"Tipo", default='fornecedor', required=True)
    estoque_id = fields.Many2one('ud.almoxarifado.estoque', u'Estoque', invisible=True, ondelete='cascade')
    fornecedor_id = fields.Many2one('ud.almoxarifado.fornecedor', u'Fornecedor')
    observacao = fields.Text(u'Observações')

    @api.one
    def get_name(self):
        self.name = "Data: {}; Quantidade: {}; Produto: {}".format(self.data_entrada.strftime('%d/%m/%Y'),
                                                                   self.quantidade, self.estoque_id.name)
