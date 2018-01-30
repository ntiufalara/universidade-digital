# encoding: UTF-8

from odoo import models, fields


class AtribuirPrevisao(models.TransientModel):
    """
    Atribui descrição do serviço realizado e muda o status para "Finalizado"
    """
    _name = 'ud.servico.finalizar_servico'

    descricao = fields.Text(u'Serviço realizado', required=True)

    def finalizar(self):
        solicitacao = self.env['ud.servico.solicitacao'].browse(self.env.context.get('active_id'))
        solicitacao.sudo().write({
            'finalizar': self.descricao,
            'state': 'finalizada'
        })
