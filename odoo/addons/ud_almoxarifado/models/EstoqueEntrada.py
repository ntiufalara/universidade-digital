# encoding: UTF-8
import logging
from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


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
    estoque_id = fields.Many2one('ud.almoxarifado.estoque', u'Item do estoque', ondelete='cascade')
    produto_id = fields.Many2one('ud.almoxarifado.produto', u'Produto', ondelete='set null', required=True)
    fornecedor_id = fields.Many2one('ud.almoxarifado.fornecedor', u'Fornecedor')
    solicitacao_id = fields.Many2one('ud.almoxarifado.solicitacao', u'Solicitação')
    observacao = fields.Text(u'Observações')
    remessa_id = fields.Many2one('ud.almoxarifado.remessa_entrada', u'Remessa')

    @api.model
    def create(self, vals):
        """
        Cria o item no estoque caso ele não exista antes de salvar
        :param vals:
        :return:
        """
        obj = super(EstoqueEntrada, self).create(vals)
        estoque_model = self.env['ud.almoxarifado.estoque']
        # Verifica a condição abaixo (se já existe) para executar a criação de um novo item de estoque
        domain_exists = [('almoxarifado_id', '=', obj.almoxarifado_id.id), ('produto_id', '=', obj.produto_id.id)]
        estoque_id = estoque_model.search(domain_exists)
        if not estoque_id:
            # Cria o item de estoque
            estoque_id = self.env['ud.almoxarifado.estoque'].create({
                'produto_id': obj.produto_id.id,
                'estoque_min': 1,
                'almoxarifado_id': obj.almoxarifado_id.id,
                'campus_id': obj.almoxarifado_id.campus_id.id,
                'polo_id': obj.almoxarifado_id.polo_id.id
            })
        # Atribui o item de estoque à entrada
        obj.estoque_id = estoque_id
        return obj

    @api.one
    def get_name(self):
        self.name = "ALM_ENTRADA_{}".format(self.id)

    def get_almoxarifado(self):
        return self.env.context.get('almoxarifado_id')

    @api.constrains('remessa_id', 'almoxarifado_id', 'name')
    def verifica_almoxarifado(self):
        if self.almoxarifado_id.id != self.remessa_id.almoxarifado_id.id:
            raise ValidationError('O almoxarifado da entrada {} precisa ser o mesmo da remessa'.format(self.name))
