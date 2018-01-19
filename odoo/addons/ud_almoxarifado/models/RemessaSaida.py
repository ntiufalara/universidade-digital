# encoding: UTF-8

from odoo import models, fields, api


class RemessaSaida(models.Model):
    """
    Saída de remessa, agrupa várias saídas de estoque
    """
    _name = 'ud.almoxarifado.remessa_saida'
    _order = 'id desc'

    name = fields.Char(u'Código', compute='get_name', readonly=True)
    data_hora = fields.Datetime(u'Data/hora', default=fields.datetime.now(), readonly=True)
    saida_ids = fields.One2many('ud.almoxarifado.saida', 'remessa_id', u'Saídas', required=True)
    campus_id = fields.Many2one('ud.campus', u'Campus', required=True)
    polo_id = fields.Many2one('ud.polo', u'Polo', domain="[('campus_id', '=', campus_id)]", required=True)
    almoxarifado_id = fields.Many2one('ud.almoxarifado.almoxarifado', u'Almoxarifado',
                                      domain="[('polo_id', '=', polo_id)]", required=True)

    @api.one
    def get_name(self):
        self.name = 'ALM_RM_SAIDA_{}'.format(self.id)
