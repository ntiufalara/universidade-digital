# encoding: UTF-8

from odoo import models, fields, api


class AtribuirResponsavel(models.TransientModel):
    """
    Usado no Wizard para atribuir um responsável à solicitação
    """
    _name = 'ud.servico.atribuir_responsavel'

    responsavel_id = fields.Many2one('ud.servico.responsavel', u'Responsável', required=True)

    def atribuir(self):
        solicitacao = self.env['ud.servico.solicitacao'].search(self.env.context.get('active_id'))
        solicitacao.write({
            'responsavel_analise_id': self.responsavel_id.id
        })
