# encoding: UTF-8

from odoo import models, fields, api


class TipoRefrigerador(models.Model):
    """
    Representa o tipo de refrigerador a ser selecionado na solicitação de serviço
    """
    _name = 'ud.servico.tipo_refrigerador'

    name = fields.Char(u'Refrigerador', required=True)
