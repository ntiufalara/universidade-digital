# encoding: UTF-8

from odoo import models, fields


class Almoxarifado(models.Model):
    """
    Cadastro de almoxarifado, localização e responsável
    """
    _name = 'ud.almoxarifado.almoxarifado'

    name = fields.Char(u'Nome')
    campus_id = fields.Many2one('ud.campus', u'Campus')
    polo_id = fields.Many2one('ud.polo', u'Polo', domain="[('campus_id', '=', campus_id)]")
    setor_id = fields.Many2one('ud.setor', u'Setor', domain="[('polo_id', '=', polo_id)]")
    observacoes = fields.Text(u'Observações')
