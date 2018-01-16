# encoding: UTF-8

from odoo import models, fields, api


class Produto(models.Model):
    """
    Representa o produto no almoxarifado
    """
    _name = 'ud.almoxarifado.produto'
    _order = 'produto asc'

    name = fields.Char(u'Produto', required=True)
    observacao = fields.Text(u'Observação')
    categoria_id = fields.Many2one('ud.almoxarifado.categoria', u'Categoria')
    fabricante_id = fields.Many2one('ud.almoxarifado.fabricante', u'Fabricante')
    almoxarifado_ids = fields.Many2many('ud.almoxarifado.almoxarifado', 'produto_almoxarifados_rel',
                                        string=u'Almoxarifados')

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
        # Cria a instancia
        obj = super(Produto, self).create(vals)
        for almoxarifado in self.almoxarifado_ids:
            self.env['ud.almoxarifado.estoque'].create({
                'produto_id': obj.id,
                'estoque_min': 1,
                'almoxarifado_id': almoxarifado.id
            })
        return obj
