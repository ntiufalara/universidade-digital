# encoding: UTF-8

from odoo import models, fields


class SolicitacaoProduto(models.Model):
    """
    Registro de solicitações de produtos do estoque.
    As solicitações reservam o produto, caso aprovado, o produto é registrado em saída
    """
    _name = 'ud.almoxarifado.solicitacao'

    _STATE = [("aguardando", "Aguardando Retirada"),
              ("entregue", "Entregue"),
              ("cancelada", "Cancelada")]

    name = fields.Char(u'Nome')
    produtos_ids = fields.One2many('ud.almoxarifado.produto.qtd', 'solicitacao_id', string=u'Produtos',
                                   required=True)
    solicitante_id = fields.Many2one('ud.employee', 'Solicitante', ondelete='restrict')
    data_hora = fields.datetime(u'Data/hora')
    setor_id = fields.Many2one('ud.setor', 'Setor', required=True)
    state = fields.Selection(_STATE, u"Status")
