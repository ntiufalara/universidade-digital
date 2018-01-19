# encoding: UTF-8

from odoo import models, fields, api


class SolicitacaoProduto(models.Model):
    """
    Registro de solicitações de produtos do estoque.
    As solicitações reservam o produto, caso aprovado, o produto é registrado em saída
    """
    _name = 'ud.almoxarifado.solicitacao'
    _order = 'id desc'

    _STATE = [("aguardando", "Aguardando Retirada"),
              ("entregue", "Entregue"),
              ("cancelada", "Cancelada")]

    name = fields.Char(u'Código', compute='get_name', readonly=True)
    produto_ids = fields.One2many('ud.almoxarifado.produto.qtd', 'solicitacao_id', string=u'Produtos',
                                  required=True)
    solicitante_id = fields.Many2one('res.users', 'Solicitante', ondelete='restrict', default=lambda self: self.env.uid)
    data_hora = fields.Datetime(u'Data/hora', default=fields.datetime.now())
    setor_id = fields.Many2one('ud.setor', 'Setor solicitante', required=True, default=lambda self: self.get_setor())
    state = fields.Selection(_STATE, u"Status")

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
