# encoding: UTF-8

from odoo import models, fields, api


class SolicitacaoProduto(models.Model):
    """
    Registro de solicitações de produtos do estoque.
    As solicitações reservam o produto, caso aprovado, o produto é registrado em saída
    """
    _name = 'ud.almoxarifado.solicitacao'
    _order = 'id desc'

    _STATE = [("aguardando", u"Aguardando Retirada"),
              ("entregue", u"Entregue"),
              ("cancelada", u"Cancelada")]

    name = fields.Char(u'Código', compute='get_name', readonly=True)
    produto_ids = fields.One2many('ud.almoxarifado.produto.qtd', 'solicitacao_id', string=u'Produtos',
                                  required=True)
    solicitante_id = fields.Many2one('res.users', 'Solicitante', ondelete='restrict', default=lambda self: self.env.uid)
    data_hora = fields.Datetime(u'Data/hora', default=fields.datetime.now())
    setor_id = fields.Many2one('ud.setor', 'Setor solicitante', required=True, default=lambda self: self.get_setor())
    state = fields.Selection(_STATE, u"Status")

    def process_domain(self):
        """
        Usado para filtrar as listas apenas com itens aos quais o responsável tem acesso.
        :return: [(), (),...]
        """
        user = self.env.user
        grupo_gerente = self.env.ref('ud_almoxarifado.group_ud_almoxarifado_gerente')
        grupo_admin = self.env.ref('ud_almoxarifado.group_ud_almoxarifado_administrador')
        grupo_solicitante = self.env.ref('ud_almoxarifado.group_ud_almoxarifado_usuario')
        domain = []
        if grupo_gerente in user.groups_id and grupo_admin not in user.groups_id:
            alm_resposavel = []
            for res in user.almoxarifado_responsavel_ids:
                for alm in res.almoxarifado_ids:
                    alm_resposavel.append(alm.id)
            domain = [('produto_ids.almoxarifado_id', 'in', list(alm_resposavel))]
        elif grupo_solicitante in user.groups_id and grupo_gerente not in user.groups_id and grupo_admin not in user.groups_id:
            domain = [('solicitante_id', '=', user.id)]
        return domain

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        domain = [] if not domain else domain
        domain += self.process_domain()
        return super(SolicitacaoProduto, self).search_read(domain, fields, offset, limit, order)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        domain = [] if not domain else domain
        domain += self.process_domain()
        return super(SolicitacaoProduto, self).read_group(domain, fields, groupby, offset, limit, orderby, lazy)

    @api.one
    def get_name(self):
        self.name = "ALM_SLC_{}".format(self.id)

    def get_setor(self):
        """
        Localiza o setor ao qual o usuário está vinculado
        :return:
        """
        for perfil in self.env.user.perfil_ids:
            if perfil.setor_id:
                return perfil.setor_id.id
        return False

    @api.model
    def create(self, vals):
        """
        Troca o status por 'aguardando' após criar a solicitação.
        Adiciona a observação: "Solicitação: ALMXX" a saída criada
        :param vals:
        :return:
        """
        vals['state'] = "aguardando"

        saida_model = self.env['ud.almoxarifado.saida']
        obj = super(SolicitacaoProduto, self).create(vals)
        for produto in obj.produto_ids:
            saida_model.sudo().create({
                'quantidade': produto.quantidade,
                'estoque_id': produto.estoque_id.id,
                'solicitacao_id': obj.id,
                'observacao': 'Nova solicitação'
            })
        return obj

    def botao_entregue(self):
        """
        Conclui a solicitação com o status 'entregue'
        :return:
        """
        self.state = 'entregue'

    def botao_cancelar(self):
        """
        Cancela a solicitação e recoloca os produtos no estoque
        :return:
        """
        entrada_model = self.env['ud.almoxarifado.entrada']
        for produto in self.produto_ids:
            entrada_model.sudo().create({
                'quantidade': produto.quantidade,
                'estoque_id': produto.estoque_id.id,
                'produto_id': produto.estoque_id.produto_id.id,
                'almoxarifado_id': produto.almoxarifado_id.id,
                'solicitacao_id': self.id,
                'observacao': 'Solicitação cancelada',
                'tipo': 'devolucao'
            })
        self.state = 'cancelada'

    def unlink(self):
        """
        Antes de apagar uma solicitação, restaura os itens no estoque
        :return:
        """
        for slc in self:
            entrada_model = self.env['ud.almoxarifado.entrada']
            for produto in slc.produto_ids:
                entrada_model.sudo().create({
                    'quantidade': produto.quantidade,
                    'estoque_id': produto.estoque_id.id,
                    'solicitacao_id': slc.id,
                    'observacao': 'Solicitação apagada',
                    'tipo': 'devolucao'
                })
        return super(SolicitacaoProduto, self).unlink()
