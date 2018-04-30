# encoding: UTF-8

from odoo import models, fields, api


class Produto(models.Model):
    """
    Representa o produto no almoxarifado
    """
    _name = 'ud.almoxarifado.produto'
    _order = 'name asc'

    name = fields.Char(u'Produto', required=True)
    observacao = fields.Text(u'Observação')
    categoria_id = fields.Many2one('ud.almoxarifado.produto.categoria', u'Categoria', required=True)
    fabricante_id = fields.Many2one('ud.almoxarifado.fabricante', u'Fabricante', required=True)
    almoxarifado_ids = fields.Many2many('ud.almoxarifado.almoxarifado', 'produto_almoxarifados_rel',
                                        string=u'Almoxarifados', required=True)
    fornecedor_ids = fields.Many2many('ud.almoxarifado.fornecedor', 'produto_fornecedor_rel', string=u'Fornecedores',
                                      required=True)

    _sql_constraints = [
        ('produto_unico', 'unique (name,categoria_id)', u'Produto já cadastrado nessa categoria!'),
    ]

    @api.model
    def create(self, vals):
        """
        Ao criar produto, cria uma instancia dele no estoque.
        Converte o nome para Caixa alta
        :param vals:
        :return: RecordSet(): Instância do objeto criado
        """
        vals['name'] = vals.get('name').upper()
        obj = super(Produto, self).create(vals)
        return obj

    def write(self, vals):
        result = super(Produto, self).write(vals)
        estoque_model = self.env['ud.almoxarifado.estoque']
        for almoxarifado in self.almoxarifado_ids:
            if not estoque_model.search([('almoxarifado_id', '=', almoxarifado.id), ('produto_id', '=', self.id)]):
                self.env['ud.almoxarifado.estoque'].create({
                    'produto_id': self.id,
                    'estoque_min': 1,
                    'almoxarifado_id': almoxarifado.id,
                    'campus_id': almoxarifado.campus_id.id,
                    'polo_id': almoxarifado.polo_id.id
                })
        return result
