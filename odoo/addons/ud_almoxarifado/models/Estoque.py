# encoding: UTF-8

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Estoque(models.Model):
    """
    Usado para controle de estoque
    """
    _name = "ud.almoxarifado.estoque"

    name = fields.Char(u'Nome', compute='get_name')
    produto_id = fields.Many2one('ud.almoxarifado.produto', u'Produto', required=True)
    categoria_id = fields.Many2one('ud.almoxarifado.produto.categoria', u'Categoria', related='produto_id.categoria_id',
                                   readonly=True)
    quantidade = fields.Integer(u'Quantidade', compute='get_quantidade')
    estoque_min = fields.Integer(u'Estoque mínimo', required=True)
    entrada_ids = fields.One2many('ud.almoxarifado.entrada', 'estoque_id', u'Entrada')
    saida_ids = fields.One2many('ud.almoxarifado.saida', 'estoque_id', u'Saída')
    campus_id = fields.Many2one('ud.campus', u'Campus', required=True)
    polo_id = fields.Many2one('ud.polo', u'Polo', required=True, domain="[('campus_id', '=', campus_id)]")
    almoxarifado_id = fields.Many2one('ud.almoxarifado.almoxarifado', u'Almoxarifado', required=True,
                                      domain="[('polo_id', '=', polo_id)]")

    _sql_constraints = [
        ('produto_almoxarifado_unico', 'unique (produto_id, almoxarifado_id)', u'Produto já cadastrado!'),
    ]

    @api.one
    def get_name(self):
        self.name = self.produto_id.name

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
            domain = [('almoxarifado_id', 'in', list(alm_resposavel))]
        return domain

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        domain = [] if not domain else domain
        domain += self.process_domain()
        if not domain:
            domain = None
        return super(Estoque, self).search_read(domain, fields, offset, limit, order)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        """
        Remove a soma do total "estoque_min" na view list padrão (no topo da lista mostra a soma de todas as linhas)
        :return:
        """
        if 'estoque_min' in fields:
            fields.remove('estoque_min')
        domain = [] if not domain else domain
        domain += self.process_domain()
        return super(Estoque, self).read_group(domain, fields, groupby, offset, limit, orderby, lazy)

    @api.constrains('estoque_min')
    def valida_estoque_min(self):
        """
        O estoque mínimo precisa ser positivo
        :return:
        """
        if self.estoque_min < 1:
            raise ValidationError('A quantidade precisa ser maior que 0')

    @api.one
    def get_quantidade(self):
        """
        Calcula a quantidade baseado nas entradas e saídas
        :return:
        """
        entradas = sum([entrada.quantidade for entrada in self.entrada_ids])
        saidas = sum([saida.quantidade for saida in self.saida_ids])
        self.quantidade = entradas - saidas
