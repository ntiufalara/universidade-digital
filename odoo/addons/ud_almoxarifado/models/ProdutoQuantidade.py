# encoding: UTF-8

from odoo import models, fields, api


class ProdutoQuantidade(models.Model):
    """
    Associa produto à quantidade na solicitação
    """
    _name = 'ud.almoxarifado.produto.qtd'

    name = fields.Char(u'Nome', compute='get_name')
    produto_id = fields.Many2one('ud.almoxarifado.produto', u'Produto', domain="[('categoria_id','=', categoria_id)]",
                                 required=True, ondelete='cascade')
    quantidade = fields.Integer(u'Quantidade', required=True)
    categoria_id = fields.Many2one('ud.almoxarifado.produto.categoria', u'Categoria', ondelete='restrict')

    campus_id = fields.Many2one('ud.campus', u'Campus', required=True)
    polo_id = fields.Many2one('ud.polo', u'Polo', )
    almoxarifado_id = fields.Many2one('ud.almoxarifado.almoxarifado', u'Almoxarifado')
    estoque_id = fields.Many2one('ud.almoxarifado.estoque', u'Estoque', required=True)
    qtd_estoque = fields.Integer(u'Quantidade em estoque', related='estoque_id.quantidade')
    solicitacao_id = fields.Many2one('ud.almoxarifado.solicitacao', u'Solicitação', invisible=True)

    _sql_constraints = [
        ('produto_solicitacao_uniq', 'unique(solicitacao_id,produto_id)',
         u'Não pode solicitar o memo produto na mesma solicitação'),
    ]

    @api.one
    def get_name(self):
        self.name = self.produto_id.name

    @api.constrains('quantidade')
    def valida_quantidade(self):
        """
        TODO: validação de acordo com o estoque
        :return:
        """
        pass

    @api.onchange('produto_id')
    def onchenge_produto(self):
        """
        TODO: Atualiza o atributo "estoque" quando de acordo com o produto selecionado
        :return:
        """
        pass
