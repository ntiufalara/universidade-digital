# encoding: UTF-8

from odoo import models, fields, api


class EstoqueEntrada(models.Model):
    """
    Entrada de estoque
    """
    _name = 'ud.almoxarifado.entrada'

    _order = 'id desc'

    name = fields.Char(u'Código', compute='get_name', readonly=True)
    data_entrada = fields.Datetime(u'Data', default=fields.datetime.now(), readonly=True)
    quantidade = fields.Integer(u'Quantidade', required=True)
    tipo = fields.Selection([
        ("fornecedor", u"Fornecedor"),
        ("estorno", u"Estorno"),
        ("devolucao", u"Devolução")
    ], u"Tipo", default='fornecedor', required=True)
    almoxarifado_id = fields.Many2one('ud.almoxarifado.almoxarifado', u'Almoxarifado',
                                      default=lambda self: self.get_almoxarifado())
    estoque_id = fields.Many2one('ud.almoxarifado.estoque', u'Produto', ondelete='cascade', required=True)
    fornecedor_id = fields.Many2one('ud.almoxarifado.fornecedor', u'Fornecedor')
    solicitacao_id = fields.Many2one('ud.almoxarifado.solicitacao', u'Solicitação')
    observacao = fields.Text(u'Observações')
    remessa_id = fields.Many2one('ud.almoxarifado.remessa_entrada', u'Remessa')

    @api.one
    def get_name(self):
        self.name = "ALM_ENTRADA_{}".format(self.id)

    def get_almoxarifado(self):
        return self.env.context.get('almoxarifado_id')
