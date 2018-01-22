# encoding: UTF-8

from odoo import models, fields, api


class TipoEquipamentoEletrico(models.Model):
    """
    Representa o tipo de equipamento elétrico a ser selecionado na solicitação de serviço
    """
    _name = 'ud.servico.tipo_equipamento_eletrico'

    name = fields.Char(u'Equipamento Elétrico', required=True)
