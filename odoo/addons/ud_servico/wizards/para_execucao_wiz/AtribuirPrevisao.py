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
    risco_de_operacao = fields.Text(u'Riscos de operação')
    medidas_preventivas = fields.Text(u'Medidas preventivas')
    epi_ids = fields.Many2many('ud.servico.epi', 'servico_para_execucao_rel', string=u'EPI')

    def atribuir(self):
        solicitacao = self.env['ud.servico.solicitacao'].browse(self.env.context.get('active_id'))
        solicitacao.sudo().message_subscribe_users([self.responsavel_execucao_id.responsavel_id.id])
        solicitacao.sudo().write({
            'previsao': self.previsao,
            'responsavel_execucao_id': self.responsavel_execucao_id.id,
            'risco_de_operacao': self.risco_de_operacao,
            'medidas_preventivas': self.medidas_preventivas,
            'epi_ids': self.epi_ids,
            'state': 'aprovada'
        })
