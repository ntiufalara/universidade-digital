# encoding: UTF-8
from odoo import models, fields
import utils


class Curso(models.Model):
    """
    Representação do Curso da Universidade.
    """
    _name = 'ud.curso'
    _description = 'Curso'
    
    name = fields.Char('Nome', size=40, help=u"Ex.: Ciência da Computação", required=True)
    polo_id = fields.Many2one('ud.polo', u'Polo', ondelete='cascade', required=True)
    coordenador_id = fields.Many2one('res.users', u'Coordenador', ondelete='cascade')
    is_active = fields.Boolean(u'Ativo?', default=True)
    description = fields.Text(u'Descrição')
    disciplina_ids = fields.One2many('ud.disciplina', 'curso_id', u'Disciplinas',)
    turno = fields.Selection(utils.TURNO, u"Turno", required=True)
    modalidade = fields.Selection(utils.MODALIDADE, u"Modalidade", required=True)

