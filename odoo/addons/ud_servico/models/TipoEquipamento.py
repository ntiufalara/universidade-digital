# encoding: UTF-8

from odoo import models, fields, api


class TipoEquipamento(models.Model):
    """
    Representa o tipo de equipamento a ser selecionado na solicitação de serviço
    """
    _name = 'ud.servico.tipo_equipamento'
    _order = 'name asc'

    name = fields.Char(u'Equipamento', required=True)
