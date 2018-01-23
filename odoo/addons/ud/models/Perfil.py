# encoding: UTF-8

from odoo import models, fields, api


class Perfil(models.Model):
    _name = 'ud.perfil'
    _order = 'id desc'

    name = fields.Char(u'Nome', compute='get_name')
    tipo_id = fields.Many2one('ud.perfil.tipo', u'Tipo', required=True)
    curso_ou_setor = fields.Selection(related='tipo_id.curso_ou_setor', store=True)
    matricula = fields.Char(u'Matrícula')
    curso_id = fields.Many2one('ud.curso', u'Curso')
    setor_id = fields.Many2one('ud.setor', u'Setor')
    pessoa_id = fields.Many2one('res.users', u'Pessoa')
    tipo_docente_id = fields.Many2one('ud.perfil.tipo_docente', u'Tipo de docente')
    bolsista = fields.Boolean(u'Bolsista')
    bolsa_id = fields.Many2one('ud.bolsa', u'Bolsa')

    _sql_constraints = [
        ('papel_uniq', 'unique (matricula,tipo_id)', u'Matricula já cadastrada (Mesmo tipo e matrícula).'),
    ]

    def get_name(self):
        self.name = 'Tipo: {}; Matrícula: {}'.format(self.tipo_id, self.matricula)

    @api.onchange('tipo_id')
    def onchange_tipo_id(self):
        """
        Limpa todos os campos caso o tipo seja alterado
        :return:
        """
        self.curso_id = False
        self.setor_id = False
        self.tipo_docente_id = False
        self.bolsista = False
        self.bolsa_id = False
