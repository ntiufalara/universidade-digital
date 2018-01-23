# encoding: UTF-8

from odoo import models, fields, api


class TipoPredial(models.Model):
    """
    Representa o tipo de ar condicionado a ser selecionado na solicitação de serviço
    """
    _name = 'ud.servico.tipo_predial'

    name = fields.Char(u'Menutenção predial', required=True)
