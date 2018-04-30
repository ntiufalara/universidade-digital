# encoding: UTF-8

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ProdutoQuantidade(models.Model):
    """
    Associa produto à quantidade na solicitação
    """
    _name = 'ud.almoxarifado.produto.qtd'

    name = fields.Char(u'Nome', compute='get_name')
    quantidade = fields.Integer(u'Quantidade', required=True)
    categoria_id = fields.Many2one('ud.almoxarifado.produto.categoria', u'Categoria', ondelete='restrict',
                                   required=True)
    campus_id = fields.Many2one('ud.campus', u'Campus', required=True)
    polo_id = fields.Many2one('ud.polo', u'Polo', required=True, domain="[('campus_id', '=', campus_id)]")
    almoxarifado_id = fields.Many2one('ud.almoxarifado.almoxarifado', u'Almoxarifado', required=True,
                                      domain="[('polo_id', '=', polo_id)]")
    estoque_id = fields.Many2one('ud.almoxarifado.estoque', u'Produto', required=True,
                                 domain="[('almoxarifado_id', '=', almoxarifado_id), "
                                        "('categoria_id', '=', categoria_id)]")
    qtd_estoque = fields.Integer(u'Qtd em estoque', related='estoque_id.quantidade', readonly=True)
    solicitacao_id = fields.Many2one('ud.almoxarifado.solicitacao', u'Solicitação', invisible=True)

    _sql_constraints = [
        ('produto_solicitacao_uniq', 'unique(solicitacao_id,estoque_id)',
         u'Não pode solicitar o memo produto na mesma solicitação'),
    ]

    @api.one
    def get_name(self):
        self.name = self.estoque_id.name

    @api.constrains('quantidade')
    def valida_quantidade(self):
        """
        Verifica se a quantidade solicitada está disponível no estoque
        :return:
        """
        if self.quantidade > self.estoque_id.quantidade:
            raise ValidationError("A quantidade para: {} não está disponível no estoque".format(self.estoque_id.name))
