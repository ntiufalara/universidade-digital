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

    def process_domain(self):
        """
        Usado para filtrar as listas apenas com itens aos quais o responsável tem acesso.
        :return: [(), (),...]
        """
        user = self.env.user
        grupo_gerente = self.env.ref('ud_almoxarifado.group_ud_almoxarifado_gerente')
        grupo_admin = self.env.ref('ud_almoxarifado.group_ud_almoxarifado_administrador')
        domain = []
        if grupo_gerente in user.groups_id and grupo_admin not in user.groups_id:
            alm_resposavel = []
            for res in user.almoxarifado_responsavel_ids:
                for alm in res.almoxarifado_ids:
                    alm_resposavel.append(alm.id)
            domain = [('almoxarifado_ids', '=', list(alm_resposavel))]
        return domain

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        domain = [] if not domain else domain
        domain += self.process_domain()
        return super(Produto, self).search_read(domain, fields, offset, limit, order)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        domain = [] if not domain else domain
        domain += self.process_domain()
        return super(Produto, self).read_group(domain, fields, groupby, offset, limit, orderby, lazy)

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

