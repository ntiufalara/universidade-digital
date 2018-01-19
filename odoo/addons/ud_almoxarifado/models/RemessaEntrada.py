# encoding: UTF-8
from odoo import models, fields, api


class RemessaEntrada(models.Model):
    """
    Entrada de remessa, agrupa várias entradas de estoque
    """
    _name = 'ud.almoxarifado.remessa_entrada'
    _order = 'id desc'

    name = fields.Char(u'Código', compute='get_name', readonly=True)
    data_hora = fields.Datetime(u'Data/hora', default=fields.datetime.now(), readonly=True)
    entrada_ids = fields.One2many('ud.almoxarifado.entrada', 'remessa_id', u'Entradas', required=True)
    campus_id = fields.Many2one('ud.campus', u'Campus', required=True)
    polo_id = fields.Many2one('ud.polo', u'Polo', domain="[('campus_id', '=', campus_id)]", required=True)
    almoxarifado_id = fields.Many2one('ud.almoxarifado.almoxarifado', u'Almoxarifado',
                                      domain="[('polo_id', '=', polo_id)]", required=True)

    @api.one
    def get_name(self):
        self.name = 'ALM_RM_ENTRADA_{}'.format(self.id)
