# encoding: UTF-8
from odoo import models, fields, api
from odoo.exceptions import ValidationError


# TODO: Continuar migração dos espaços e das disciplinas
class Disciplina(models.Model):
    """
    Classe que representa os campos do formulário Disciplina (Associada com a classe Curso).
    """
    _name = 'ud.disciplina'
    _description = 'Disciplina'

    codigo = fields.Char(u'Código', size=15, required=True)
    name = fields.Char(u'Nome', size=40, required=True)
    ch = fields.Integer(u'Carga Horária', size=10, required=True)
    descricao = fields.Text(u'Descrição')
    curso_id = fields.Many2one('ud.curso', u'Curso', ondelete='cascade',)

    @api.one
    @api.constrains('ch')
    def valida_ch(self):
        if self.ch < 1:
            raise ValidationError(u'Carga horária não possui um número válido')
