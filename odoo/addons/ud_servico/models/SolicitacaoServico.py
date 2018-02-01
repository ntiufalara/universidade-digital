# encoding: UTF-8

from odoo import models, fields, api
from odoo.addons.ud_servico.models import utils


class SolicitacaoServico(models.Model):
    """
    Solicitação para geração de ordem de serviço
    """
    _name = 'ud.servico.solicitacao'
    _order = 'data desc'

    name = fields.Char(u'Código', compute="get_name")
    solicitante_id = fields.Many2one('res.users', u'Solicitante', required=True, default=lambda self: self.env.uid)
    matricula = fields.Char(u'Matrícula', compute='get_matricula')
    setor_id = fields.Many2one('ud.setor', u'Setor', compute='get_setor')
    email = fields.Char(u'E-mail', related='solicitante_id.email')
    telefone = fields.Char(u'Telefone', related='solicitante_id.telefone_fixo')
    data = fields.Datetime(u'Data/hora', readonly=True, default=fields.datetime.now())
    state = fields.Selection(utils.STATUS, u'Status', default='nova')
    descricao = fields.Text(u'Descrição', required=True)
    # Valores de execução de serviço e cancelamento
    data_cancelamento = fields.Datetime(u'Data de cancelamento')
    motivo_cancelamento = fields.Text(u'Motivo cancelamento')
    responsavel_analise_id = fields.Many2one('ud.servico.responsavel', u'Responsável por análise', ondelete='restrict')
    responsavel_execucao_id = fields.Many2one('ud.servico.responsavel', u'Responsável por execução', ondelete='restrict')
    previsao = fields.Date(u'Previsão para execução')
    execucao = fields.Text(u'Descrição do serviço')
    data_execucao = fields.Datetime(u'Data/hora execução')
    finalizar = fields.Text(u'Serviço executado')
    # Classificação das ordens de serivço
    tipo_manutencao_id = fields.Many2one('ud.servico.tipo_manutencao', u'Manutenção', required=True)
    tipo_equipamento_id = fields.Many2one('ud.servico.tipo_equipamento', u'Equipamentos')
    tipo_equipamento_eletrico_id = fields.Many2one('ud.servico.tipo_equipamento_eletrico', u'Equipamento elétrico')
    tipo_refrigerador_id = fields.Many2one('ud.servico.tipo_refrigerador', u'Refrigerador')
    tipo_ar_condicionado_id = fields.Many2one('ud.servico.tipo_ar', u'Ar condicionado')
    marca_equipamento = fields.Char(u'Marca')
    modelo_equipamento = fields.Char(u'Modelo')
    tipo_predial_id = fields.Many2one('ud.servico.tipo_predial', u'Tipo')
    tipo_instalacoes_id = fields.Many2one('ud.servico.tipo_instalacoes', u'Instalações')
    denominacao = fields.Char(u'Denominação')
    numero_patrimonio = fields.Char(u'Patrimônimo nº')
    # Local
    campus_id = fields.Many2one('ud.campus', u'Campus', required=True, default=lambda self: self.get_campus())
    polo_id = fields.Many2one('ud.polo', u'Polo', required=True, domain="[('campus_id', '=', campus_id)]",
                              default=lambda self: self.get_polo())
    espaco_id = fields.Many2one('ud.espaco', u'Espaço', required=True, domain="[('polo_id', '=', polo_id)]")
    bloco_id = fields.Many2one('ud.bloco', u'Bloco', related='espaco_id.bloco_id')
    detalhes_espaco = fields.Char(u'Detalhes do espaço')
    # Destino de movoimentação de materiais
    campus_destino_id = fields.Many2one('ud.campus', u'Campus')
    polo_destino_id = fields.Many2one('ud.polo', u'Polo', domain="[('campus_id', '=', campus_destino_id)]")
    espaco_destino_id = fields.Many2one('ud.espaco', u'Espaço', domain="[('polo_id', '=', polo_destino_id)]")
    bloco_destino_id = fields.Many2one('ud.bloco', u'Bloco', related='espaco_destino_id.bloco_id')
    detalhes_espaco_destino = fields.Char(u'Detalhes do espaço')

    @api.one
    def get_name(self):
        self.name = 'SRV_SLC_{}'.format(self.id)

    @api.one
    def get_matricula(self):
        """
        Localiza e atribui a ultima matrícula cadastrada
        :return:
        """
        for papel in self.env.user.perfil_ids:
            self.matricula = papel.matricula
            break

    @api.one
    def get_setor(self):
        """
        Localiza e atribui o setor da última matricula cadastrada
        :return:
        """
        for papel in self.env.user.perfil_ids:
            self.setor_id = papel.setor_id
            break

    def get_campus(self):
        """
        Carrega o Campus atrelado a matricula do usuário por padrão
        :return:
        """
        for papel in self.env.user.perfil_ids:
            return papel.setor_id.polo_id.campus_id.id
        return False

    def get_polo(self):
        """
        Carrega o Polo atrelado a matricula do usuário por padrão
        :return:
        """
        for papel in self.env.user.perfil_ids:
            return papel.setor_id.polo_id.id
        return False
