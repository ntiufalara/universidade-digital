# encoding: UTF-8
from odoo import models, fields, api


class EstoqueSaida(models.Model):
    """
    Saída de estoque
    """
    _name = 'ud.almoxarifado.saida'
    _order = 'id desc'

    name = fields.Char(u'Código', compute='get_name', readonly=True)
    data_saida = fields.Datetime(u'Data', default=fields.datetime.now(), readonly=True)
    quantidade = fields.Integer(u'Quantidade', required=True)
    observacao = fields.Text(u'Observações')
    almoxarifado_id = fields.Many2one('ud.almoxarifado.almoxarifado', u'Almoxarifado',
                                      default=lambda self: self.get_almoxarifado())
    estoque_id = fields.Many2one('ud.almoxarifado.estoque', u'Estoque', ondelete='cascade', required=True)
    solicitacao_id = fields.Many2one('ud.almoxarifado.solicitacao', u'Solicitação')
    remessa_id = fields.Many2one('ud.almoxarifado.remessa_saida', u'Remessa')

    @api.one
    def get_name(self):
        self.name = "ALM_SAIDA_{}".format(self.id)

    def get_almoxarifado(self):
        return self.env.context.get('almoxarifado_id')
