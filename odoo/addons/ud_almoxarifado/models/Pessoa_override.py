# encoding: UTF-8
from odoo import models, fields


class Pessoa(models.Model):
    """
    Classe que representa os campos do formulário Pessoa.
    """
    _name = 'res.users'
    _inherit = 'res.users'

    almoxarifado_responsavel_ids = fields.One2many('ud.almoxarifado.responsavel', 'pessoa_id',
                                                   u'Responsável por almoxarifado')
