# encoding: UTF-8

from odoo import models, fields, api


class ResponsavelReserva(models.Model):
    _name = 'ud.reserva.responsavel'

    name = fields.Char(u'Nome', related='pessoa_id.name')
    pessoa_id = fields.Many2one('res.users', u'Responsável', required=True)
    campus_id = fields.Many2one('ud.campus', u'Campus', required=True)
    polo_id = fields.Many2one('ud.polo', u'Polo', required=True)
    espaco_ids = fields.Many2many('ud.espaco', 'reserva_responsavel_espaco_rel', string=u'Espaço', required=True)

    _sql_constraints = [
        ('pessoa_id_uniq', 'unique(pessoa_id)',
         "Encontramos outro registro para a mesma pessoa, por favor edite ou apague o outro registro pra salvar.")
    ]

    @api.model
    def create(self, vals):
        obj = super(ResponsavelReserva, self).create(vals)
        obj.pessoa_id.groups_id |= self.env.ref('ud_reserva.gerente_reserva')
        return obj
