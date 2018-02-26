# encoding: UTF-8

from odoo import models, fields, api


class Setor(models.Model):
    """
    Sobrescreve setor para adicionar os campos abaixo
    """
    _name = 'ud.setor'
    _inherit = 'ud.setor'

    emite_portaria = fields.Boolean(u'Emite portaria')
    responsavel_id = fields.Many2one('res.users', u'Responsável')
