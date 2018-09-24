# encoding: UTF-8
import logging

import utils
from odoo import models, fields

_logger = logging.getLogger(__name__)


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
    disciplina_ids = fields.One2many('ud.disciplina', 'curso_id', u'Disciplinas', )
    turno = fields.Selection(utils.TURNO, u"Turno")
    modalidade_id = fields.Many2one('ud.curso.modalidade', u"Modalidade", required=True)

    def load_from_openerp7_cron(self):
        """
        Realiza a sincronização dos Cursos com o Openerp 7
        :return:
        """
        MODALIDADE = [("l", u"Licenciatura"), ("lp", u"Licenciatura Plena"), ("b", u"Bacharelado"),
                      ('e', u'Especialização')]

        _logger.info(u'Sincronizando Cursos com o Openerp 7')
        import xmlrpclib
        # Conectando ao servidor externo
        server_oe7 = self.env['ud.server.openerp7'].search([('db', '=', 'ud')])
        url, db, username, password = server_oe7.url, server_oe7.db, server_oe7.username, server_oe7.password
        try:
            auth = xmlrpclib.ServerProxy("{}/xmlrpc/common".format(url))
            uid = auth.login(db, username, password)
        except:
            return
        server = xmlrpclib.ServerProxy("{}/xmlrpc/object".format(url))
        curso_ids = server.execute(db, uid, password, 'ud.curso', 'search', [])
        curso_objs = server.execute_kw(db, uid, password, 'ud.curso', 'read', [curso_ids])

        for curso in curso_objs:
            new_curso = self.search([('name', '=', curso['name'])])
            polo_id = self.env['ud.polo'].search([('name', '=', curso['polo_id'][1])])

            # Pula caso o polo ainda não exista no banco de dados
            if not polo_id:
                continue

            modalidade_name = dict(MODALIDADE)[curso['modalidade']] if curso['modalidade'] else 'Licenciatura'
            modalidade_id = self.env['ud.curso.modalidade'].search([('name', '=', modalidade_name)])

            if not new_curso:
                self.create({
                    'name': curso['name'],
                    'polo_id': polo_id.id,
                    'modalidade_id': modalidade_id.id
                })
