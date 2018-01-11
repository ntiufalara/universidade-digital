# encoding: UTF-8
import re
import pytz
from datetime import time, datetime, timedelta

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AdicionarDiasWizard(models.TransientModel):
    """
    Descrição: Gerador de dias para reserva de espaço
    """
    _name = 'ud.reserva.adicionar_dias_wizard'

    data_inicio = fields.Date(u'Data de início', required=True,
                              default=datetime.now(tz=pytz.timezone('America/Maceio')).date())
    data_fim = fields.Date(u'Data de fim', required=True)
    hora_inicio = fields.Char(u'Hora de início', required=True)
    hora_fim = fields.Char(u'Hora de fim', required=True)
    espaco_ids = fields.Many2many('ud.espaco', 'dia_wiz_espaco_rel', string=u'Espaços', required=True)

    todos = fields.Boolean(u'Todos')
    dias_uteis = fields.Boolean(u'Dias úteis')
    domingo = fields.Boolean(u'Domingo')
    segunda = fields.Boolean(u'Segunda-feira')
    terca = fields.Boolean(u'Terça-feira')
    quarta = fields.Boolean(u'Quarta-feira')
    quinta = fields.Boolean(u'Quinta-feira')
    sexta = fields.Boolean(u'Sexta-feira')
    sabado = fields.Boolean(u'Sábado')

    @api.one
    @api.constrains('data_inicio')
    def valida_data_inicio(self):
        """
        Verifica se a data de início é maior ou igual a hoje
        :return:
        """
        # Cosidera a Timezone do usuário ou a "America/Maceio" como padrão
        tz = self._context.get('tz') if self._context.get('tz') else 'America/Maceio'
        hoje = datetime.now(tz=pytz.timezone(tz)).replace(hour=0, minute=0, second=0, microsecond=0)
        data_inicio = pytz.timezone(tz).localize(datetime.strptime(self.data_inicio, '%Y-%m-%d'))
        if data_inicio < hoje:
            raise ValidationError('A data de início deve ser igual ou superior a data de hoje.')

    @api.one
    @api.constrains('data_fim', 'data_inicio')
    def valida_data_fim(self):
        """
        Verifica se a data de fim é maior ou igual a data de início
        :return:
        """
        tz = self._context.get('tz') if self._context.get('tz') else 'America/Maceio'
        data_inicio = pytz.timezone(tz).localize(datetime.strptime(self.data_inicio, '%Y-%m-%d'))
        data_fim = pytz.timezone(tz).localize(datetime.strptime(self.data_fim, '%Y-%m-%d'))
        if data_fim == data_inicio:
            raise ValidationError('Use a lista no formulário de reserva para adicionar um único dia ao agendamento.')
        if data_fim < data_inicio:
            raise ValidationError('A data de fim deve ser maior ou igual a data de início.')

    @staticmethod
    def str_to_time(hora_str, tz=None):
        return time(int(hora_str[:2]), int(hora_str[3:]), tzinfo=tz)

    @staticmethod
    def valida_hora(hora, label):
        """
        Verifica o formato e as valores da hora estão corretos.
        :param hora:
        :param label:
        :return: Instância de datetime.time(), com o horário válido passadp
        :raise: ValidationError caso o formato ou os valores estejam incorretos
        """
        # Usado para a validação do formato de hora
        time_format = r'\d{2}:\d{2}'
        if not re.match(time_format, hora):
            raise ValidationError('Por favor verifique se a {} foi digitada corretamente.'.format(label))
        hora_hdgts = int(hora[:2])
        hora_mdgts = int(hora[3:])
        if hora_hdgts > 23 or hora_hdgts < 0 or hora_mdgts > 59 or hora_mdgts < 0:
            raise ValidationError('Por favor verifique se o valor da {} está correto'.format(label))
        return time(hora_hdgts, hora_mdgts)

    @api.one
    @api.constrains('hora_inicio', 'hora_fim')
    def valida_hora_fim(self):
        """
        Verifica se a hora de fim é maior que a hora de início
        :return:
        """
        inicio = self.valida_hora(self.hora_inicio, 'hora de início')
        fim = self.valida_hora(self.hora_fim, 'hora de fim')
        if fim <= inicio:
            raise ValidationError('A hora de fim deve ser maior que a hora de início.')

    @api.one
    @api.constrains('todos', 'dias_uteis', 'domingo', 'segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado')
    def valida_dias_marcados(self):
        """
        Verifica se algum desses campos foi selecionado.
        Ao menos uma das opções deve ser selecionada.
        :return:
        """
        opt_any = any(
            [self.todos, self.dias_uteis, self.domingo, self.segunda, self.terca, self.quarta, self.quinta, self.sexta,
             self.sabado]
        )
        if not opt_any:
            raise ValidationError(
                'Por favor, selecione ao menos um dia na semana ou algum dos campos "todos", "dias úteis"')

    @api.onchange('todos', 'dias_uteis')
    def onchange_dias(self):
        """
        Limpa os campos em caso de troca de valores
        :return:
        """
        self.domingo = self.segunda = self.terca = self.quarta = self.quinta = self.sexta = self.sabado = False

    def adicionar(self):
        """
        Gera os dias de acordo com as preferências marcadas no formulário
        :return:
        """
        tz = self._context.get('tz') if self._context.get('tz') else 'America/Maceio'
        data_inicio = datetime.strptime(self.data_inicio, '%Y-%m-%d')
        data_fim = datetime.strptime(self.data_fim, '%Y-%m-%d')

        um_dia = timedelta(days=1)
        dias_uteis = range(5)
        dia_reserva = self.env['ud.reserva.dia']
        while data_inicio != (data_fim + um_dia):
            dia_da_semana = data_inicio.weekday()
            if self.todos\
                    or (self.dias_uteis and dia_da_semana in dias_uteis)\
                    or (self.segunda and dia_da_semana == 0)\
                    or (self.terca and dia_da_semana == 1)\
                    or (self.quarta and dia_da_semana == 2)\
                    or (self.quinta and dia_da_semana == 3)\
                    or (self.sexta and dia_da_semana == 4)\
                    or (self.sabado and dia_da_semana == 5)\
                    or (self.domingo and dia_da_semana == 6):
                for espaco in self.espaco_ids:
                    dia_reserva.create({
                        'data_inicio': pytz.timezone(tz).localize(datetime.combine(
                            data_inicio.date(),
                            self.str_to_time(self.hora_inicio)
                        )).astimezone(pytz.utc),
                        'data_fim': pytz.timezone(tz).localize(datetime.combine(
                            data_inicio.date(),
                            self.str_to_time(self.hora_fim)
                        )).astimezone(pytz.utc),
                        'reserva_id': self._context.get('active_id'),
                        'espaco_id': espaco.id
                    })
            data_inicio += um_dia
