# encoding: UTF-8

from odoo import models, fields, api


class AtribuirResponsavel(models.TransientModel):
    """
    Usado no Wizard para atribuir um responsável à solicitação
    """
    _name = 'ud.servico.atribuir_responsavel'

    responsavel_id = fields.Many2one('ud.servico.responsavel', u'Responsável', required=True,
                                     domain="['|', ('tipo', '=', 'analise'), ('tipo', '=', 'ambos')]")

    def atribuir(self):
        solicitacao = self.env['ud.servico.solicitacao'].browse(self.env.context.get('active_id'))
        solicitacao.sudo().message_subscribe_users([self.responsavel_id.responsavel_id.id])
        messagem = u"""
                <p>Sua solicitação está em análise</p>
                <span><strong>Responsável por análise: </strong></span><span>{}</span><br>
                """.format(self.responsavel_id.name)
        solicitacao.message_post(messagem, message_type='email', subtype='mt_comment')
        solicitacao.sudo().write({
            'responsavel_analise_id': self.responsavel_id.id,
            'state': 'analise'
        })
