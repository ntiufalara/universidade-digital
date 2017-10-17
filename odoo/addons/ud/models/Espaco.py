# encoding: UTF-8
from odoo import models, fields, api


class Espaco(models.Model):
    """
    Classe que representa a entidade Espaço.
    """
    _name = 'ud.espaco'

    name = fields.Char(u'Nome', required=True)
    capacidade = fields.Integer(u'Capacidade', required=True, help=u"Número de pessoas.")
    permite_reserva = fields.Boolean(u'Permitir Reserva')
    campus_id = fields.Many2one('ud.campus', u'Campus', required=True)
    polo_id = fields.Many2one('ud.polo', u'Polo', required=True, ondelete='cascade')
    bloco_id = fields.Many2one('ud.bloco', u'Bloco', required=True, ondelete='cascade')
    informacoes_adicionais = fields.Text(u'Descrição')
    responsavel_ids = fields.Many2many('res.users', 'ud_espaco_responsavel', string=u'Responsável')

    @api.onchange('polo_id')
    def limpa_bloco(self):
        """
        Limpa o campo bloco se o polo não pertencer a ele.
        """
        campos = ["polo_id"]
        valores = {}
        for campo in campos:
            valores[campo] = ""
        return {'value': valores}
