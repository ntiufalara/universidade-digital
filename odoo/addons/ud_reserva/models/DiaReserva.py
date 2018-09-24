# encoding: UTF-8
import pytz
from datetime import datetime, timedelta

from odoo import models, fields, api
from odoo.addons.ud_reserva.models import utils
from odoo.exceptions import ValidationError


class DiaReserva(models.Model):
    """
    Descrição: Representa a unidade de Dia na reserva
    """
    _name = 'ud.reserva.dia'

    name = fields.Char(u'Nome', compute='get_name')
    data_inicio = fields.Datetime(u'Data/Hora de início', required=True)
    data_fim = fields.Datetime(u'Data/Hora de fim', required=True)
    reserva_id = fields.Many2one('ud.reserva', u'Reserva', ondelete='cascade')
    espaco_id = fields.Many2one('ud.espaco', u'Espaço', required=True, ondelete='cascade')
    name_reserva = fields.Char(u'Reserva', related='reserva_id.name')
    state = fields.Selection(utils.STATUS_RESERVA, string=u'Status', related='reserva_id.state')

    @api.one
    def get_name(self):
        self.name = self.reserva_id.name

    @api.one
    @api.constrains('data_inicio')
    def valida_agendamento_hoje(self):
        """
        Caso a data de agendamento seja hoje, verifica se a hora de início está no futuro
        :return:
        """
        hoje = fields.datetime.fromordinal(fields.date.today().toordinal())
        data_inicio = fields.datetime.strptime(self.data_inicio, '%Y-%m-%d %H:%M:%S')
        tz = self._context.get('tz') if self._context.get('tz') else 'America/Maceio'

        if data_inicio == hoje:
            agora = fields.datetime.now(tz=pytz.timezone(tz)).time()
            hora_inicio = self.data_inicio.time()
            if hora_inicio < agora:
                raise ValidationError('A hora de início deve ser maior que a hora atual.')

    @api.one
    @api.constrains('data_inicio', 'data_fim')
    def valida_intervalo_reserva(self):
        """
        Verifica se o intervalo de tempo já está reservado
        :return:
        """
        inicio_fechado = self.search([('data_inicio', '<=', self.data_inicio), ('data_fim', '>=', self.data_inicio),
                                      ('state', '!=', 'cancelada'), ('espaco_id', '=', self.espaco_id.id),
                                      ('id', '!=', self.id)])
        fim_fechado = self.search([('data_inicio', '<=', self.data_fim), ('data_fim', '>=', self.data_fim),
                                   ('state', '!=', 'cancelada'), ('espaco_id', '=', self.espaco_id.id),
                                   ('id', '!=', self.id)])
        inicio_aberto = self.search([('data_inicio', '>=', self.data_inicio), ('data_inicio', '<=', self.data_fim),
                                     ('state', '!=', 'cancelada'), ('espaco_id', '=', self.espaco_id.id),
                                     ('id', '!=', self.id)])
        fim_aberto = self.search([('data_fim', '<=', self.data_fim), ('data_fim', '>=', self.data_inicio),
                                  ('state', '!=', 'cancelada'), ('espaco_id', '=', self.espaco_id.id),
                                  ('id', '!=', self.id)])
        if inicio_fechado or fim_fechado or inicio_aberto or fim_aberto:
            raise ValidationError('Este horário não está disponível. Há outra reserva neste intervalo de horário'
                                  ' no mesmo espaço.')

    @api.constrains('data_inicio', 'data_fim')
    def valida_dia_reserva(self):
        """
        Verifica se as datas de início e fim são no mesmo dia
        :return:
        """
        data_inicio = fields.datetime.strptime(self.data_inicio, '%Y-%m-%d %H:%M:%S')
        data_fim = fields.datetime.strptime(self.data_fim, '%Y-%m-%d %H:%M:%S')
        if data_inicio.date() != data_fim.date():
            data_inicio = data_inicio - timedelta(hours=3)
            data_fim = data_fim - timedelta(hours=3)
            if data_inicio.date() != data_fim.date():
                raise ValidationError('O início e o fim devem ser no mesmo dia')

    @api.constrains('reserva_id', 'data_inicio', 'data_fim', 'espaco_id')
    def valida_responsavel(self):
        """
        Verifica se o usuário é o solicitante ou o responsável pelo espaço.
        :return:
        :raise: ValidationError: Quando o usuário não se encaixa na regra
        """
        usuario = self.env.user
        grupo_gerente = self.env.ref('ud_reserva.gerente_reserva')
        if grupo_gerente in usuario.groups_id and self.reserva_id.solicitante_id != usuario:
            self.reserva_id.verifica_responsavel()
