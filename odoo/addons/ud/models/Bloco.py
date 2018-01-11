# encoding: UTF-8
from odoo import models, fields


class Bloco(models.Model):
    """
    Representação do Bloco (local dentro do polo)
    """
    _name = 'ud.bloco'
    _description = u'Bloco'

    _order = "name"

    name = fields.Char(u'Bloco', size=80, required=True)
    polo_id = fields.Many2one('ud.polo', u'Polo', ondelete='cascade', invisible=True)
    campus_id = fields.Char(related='polo_id.campus_id.name', string=u'Campus')

