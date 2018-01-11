# encoding: UTF-8

from odoo import models, fields, api


class PerfilTipo(models.Model):
    _name = 'ud.perfil.tipo'

    name = fields.Char(u'Tipo', required=True)
    curso_ou_setor = fields.Selection([
        ('curso', 'Curso'), ('setor', 'Setor')
    ])
