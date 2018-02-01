# encoding: UTF-8

from odoo import models, fields


class AtribuirPrevisao(models.TransientModel):
    """
    Atribui a previsão para exução do serviço e muda o status para "Encaminhado p/ execução"
    """
    _name = 'ud.servico.atribuir_previsao'

    previsao = fields.Date(u'Previsão para execução', required=True)
    responsavel_execucao_id = fields.Many2one('ud.servico.responsavel', u'Responsável por execução',
                                              domain="[('tipo', 'in', ['execucao', 'ambos'])]", required=True)

    def atribuir(self):
        solicitacao = self.env['ud.servico.solicitacao'].browse(self.env.context.get('active_id'))
        solicitacao.sudo().write({
            'previsao': self.previsao,
            'responsavel_execucao_id': self.responsavel_execucao_id.id,
            'state': 'aprovada'
        })
