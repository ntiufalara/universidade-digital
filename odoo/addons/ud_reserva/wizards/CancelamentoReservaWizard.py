# encoding: UTF-8
import pytz

from odoo import models, fields


class CancelamentoReservaWizard(models.TransientModel):
    _name = 'ud.reserva.cancelamento_reserva_wizard'

    motivo = fields.Text(u'Motivo')
    data_cancelamento = fields.Datetime(u'Data?hora cancelamento', default=lambda self: self.get_data_cancelamento())

    def get_data_cancelamento(self):
        return fields.datetime.now()

    def cancelar(self):
        reserva = self.env['ud.reserva'].browse(self._context.get('active_id'))
        if not reserva.motivo_cancelamento:
            reserva.cancelar(self.motivo, self.data_cancelamento)
