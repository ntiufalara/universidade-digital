# encoding: UTF-8

from odoo import models, fields, api


class ProdutoCategoria(models.Model):
    """

    """
    _name = 'ud.almoxarifado.produto.categoria'
    _order = 'name asc'

    name = fields.Char(u'Categoria', required=True)

    _sql_constraints = [('unique_name', 'unique(name)', u"Categoria já cadastrada!")]

    @api.model
    def create(self, vals):
        """
        Converte o nome para Caixa alta
        :param vals:
        :return:
        """
        vals['name'] = vals.get("name").upper()
        return super(ProdutoCategoria, self).create(vals)
