# encoding: UTF-8

from odoo import models, fields


class CancelarServico(models.TransientModel):
    """
    Atribui os dados de execução do serviço a solicitação/Ordem de serviço
    """
    _name = 'ud.servico.cancelar_servico'

    motivo = fields.Text(u'Motivo', required=True)
    data = fields.Date(u'Data de cancelamento', required=True, default=fields.datetime.now())

    def cancelar(self):
        solicitacao = self.env['ud.servico.solicitacao'].browse(self.env.context.get('active_id'))
        solicitacao.sudo().write({
            'motivo_cancelamento': self.motivo,
            'data_cancelamento': self.data,
            'state': 'cancelada'
        })