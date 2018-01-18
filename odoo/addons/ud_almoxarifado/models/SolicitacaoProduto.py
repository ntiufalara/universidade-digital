# encoding: UTF-8

from odoo import models, fields, api


class SolicitacaoProduto(models.Model):
    """
    Registro de solicitações de produtos do estoque.
    As solicitações reservam o produto, caso aprovado, o produto é registrado em saída
    """
    _name = 'ud.almoxarifado.solicitacao'

    _STATE = [("aguardando", "Aguardando Retirada"),
              ("entregue", "Entregue"),
              ("cancelada", "Cancelada")]

    name = fields.Char(u'Nome', compute='get_name')
    produto_ids = fields.One2many('ud.almoxarifado.produto.qtd', 'solicitacao_id', string=u'Produtos',
                                  required=True)
    solicitante_id = fields.Many2one('res.users', 'Solicitante', ondelete='restrict', default=lambda self: self.env.uid)
    data_hora = fields.Datetime(u'Data/hora', default=fields.datetime.now())
    setor_id = fields.Many2one('ud.setor', 'Setor', required=True, default=lambda self: self.get_setor())
    state = fields.Selection(_STATE, u"Status")

    @api.one
    def get_name(self):
        self.name = 'Solicitante: {}; Data: {}; Setor: {}'.format(self.solicitante_id.name,
                                                                  self.data_hora.strftime('%d/%m/%Y'),
                                                                  self.setor_id.name)

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
        Troca o status por 'aguardando' após criar a solicitação
        :param vals:
        :return:
        """
        vals['state'] = "aguardando"
        return super(SolicitacaoProduto, self).create(vals)

    def write(self, vals):
        """
        Restaura a quantidade de produtos caso o produto seja removido da lista de produtos
        TODO: Impl
        :param vals:
        :return:
        """
        return super(SolicitacaoProduto, self).write(vals)

    def botao_entregue(self):
        """
        Conclui a solicitação com o status 'entregue'
        :return:
        """
        self.state = 'entregue'

    def botao_cancelar(self):
        """
        Cancela a solicitação e restaura as quantidade do estoque
        TODO: Impl
        :return:
        """
        pass
