# encoding: UTF-8

from odoo import models, fields, api


class TipoInstalacoes(models.Model):
    """
    Representa o tipo de ar condicionado a ser selecionado na solicitação de serviço
    """
    _name = 'ud.servico.tipo_instalacoes'

    name = fields.Char(u'Instalação', required=True)
