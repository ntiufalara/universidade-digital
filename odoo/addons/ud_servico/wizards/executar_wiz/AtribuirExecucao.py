# encoding: UTF-8

from odoo import models, fields


class AtribuirExecucao(models.TransientModel):
    """
    Atribui os dados de execução do serviço a solicitação/Ordem de serviço
    """
    _name = 'ud.servico.atribuir_execucao'

    descricao = fields.Text(u'Descrição', required=True)
    data_execucao = fields.Date(u'Data de execução', required=True)

    def atribuir(self):
        solicitacao = self.env['ud.servico.solicitacao'].browse(self.env.context.get('active_id'))
        solicitacao.sudo().write({
            'execucao': self.descricao,
            'data_execucao': self.data_execucao,
            'state': 'execucao',
        })
