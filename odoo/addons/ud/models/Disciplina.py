# encoding: UTF-8
import logging
from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


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
    curso_id = fields.Many2one('ud.curso', u'Curso', ondelete='cascade', )
    periodo = fields.Char(u'Período')

    @api.one
    @api.constrains('ch')
    def valida_ch(self):
        if self.ch < 1:
            raise ValidationError(u'Carga horária não possui um número válido')

    def load_from_openerp7_cron(self):
        """
        Realiza a sincronização das Disciplinas com o Openerp 7
        :return:
        """
        MODALIDADE = [("l", u"Licenciatura"), ("lp", u"Licenciatura Plena"), ("b", u"Bacharelado"),
                      ('e', u'Especialização')]

        _logger.info(u'Sincronizando Disciplinas com o Openerp 7')
        import xmlrpclib
        # Conectando ao servidor externo
        server_oe7 = self.env['ud.server.openerp7'].search([('db', '=', 'ud')])
        url, db, username, password = server_oe7.url, server_oe7.db, server_oe7.username, server_oe7.password
        try:
            auth = xmlrpclib.ServerProxy("{}/xmlrpc/common".format(url))
            uid = auth.login(db, username, password)
        except:
            _logger.error(u'Não foi possível conectar com o servidor Openerp 7')
            return
        server = xmlrpclib.ServerProxy("{}/xmlrpc/object".format(url))
        disciplina_ids = server.execute(db, uid, password, 'ud.disciplina', 'search', [])
        disciplina_objs = server.execute_kw(db, uid, password, 'ud.disciplina', 'read', [disciplina_ids])

        for disciplina in disciplina_objs:
            if not disciplina['ud_disc_id']:
                continue
            curso = self.env['ud.curso'].search([('name', '=', disciplina['ud_disc_id'][1])])
            if not curso:
                _logger.error(u'O curso não está cadastrado')
                continue
            new_disciplina = self.search(
                [('name', '=', disciplina['name']), ('curso_id.name', '=', disciplina['ud_disc_id'][1])]
            )
            if not new_disciplina:
                self.create({
                    'name': disciplina['name'],
                    'ch': disciplina['ch'],
                    'periodo': disciplina['periodo'],
                    'curso_id': curso.id,
                    'codigo': disciplina['codigo'],
                    'descricao': disciplina['descricao'] if disciplina['descricao'] else ''
                })
                _logger.info(u'Disciplina criada: {}'.format(disciplina['name']))
