# encoding: UTF-8

from odoo import models, fields, api
from odoo.addons.ud_servico.models import utils


class SolicitacaoServico(models.Model):
    """
    Solicitação para geração de ordem de serviço
    """
    _name = 'ud.servico.solicitacao'

    name = fields.Char(u'Código', compute="get_name")
    solicitante_id = fields.Many2one('res.users', u'Solicitante', rrquired=True)
    matricula = fields.Char(u'Matrícula', compute='get_matricula')
    setor = fields.Char(u'Setor', compute='get_setor')
    email = fields.Char(u'E-mail', related='solicitante_id.email')
    telefone = fields.Char(u'Telefone', related='solicitante_id.telefone')
    data = fields.Datetime(u'Data/hora', readonly=True, default=fields.datetime.now())
    state = fields.Selection(utils.STATUS, u'Status', default='nova')
    # Valores de execução de serviço e cancelamento
    data_cancelamento = fields.Datetime(u'Data de cancelamento')
    motivo_cancelamento = fields.Text(u'Motivo cancelamento')
    responsavel_id = fields.Many2one('ud.servico.responsavel', u'Responsável')
    previsao = fields.Date(u'Previsão para execução')
    execucao = fields.Text(u'Descrição do serviço')
    data_execucao = fields.Datetime(u'Data/hora execução')
    finalizar = fields.Text(u'Serviço executado')
    # Classificação das ordens de serivço
    tipo_manutencao_id = fields.Many2one('ud.servico.tipo_manutencao', u'Manutenção', required=True)
    tipo_equipamento_id = fields.Many2one('ud.servico.tipo_equipamento', u'Equipamentos')
    tipo_equipamento_eletrico_id = fields.Many2one('ud.servico.tipo_equipamento_eletrico', u'Equipamento elétrico')
    tipo_refrigerador_id = fields.Many2one('ud.servico.tipo_refrigerador', u'Refrigerador')
    denominacao = fields.Char(u'Denominação')

    @api.one
    def get_name(self):
        self.name = 'SRV_SLC_{}'.format(self.id)
