# encoding: UTF-8

from odoo import models, fields


class PerfilTipoDocente(models.Model):
    _name = 'ud.perfil.tipo_docente'

    name = fields.Char(u'Tipo de docente')

