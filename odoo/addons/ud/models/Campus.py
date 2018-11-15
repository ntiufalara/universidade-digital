# encoding: UTF-8
import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class Campus(models.Model):
    _name = 'ud.campus'

    name = fields.Char(u'Nome', size=40, required=True, help=u"Ex.: Arapiraca, Sertão, Sede etc.")
    diretor = fields.Many2one('res.users', u'Diretor', )
    diretor_academico = fields.Many2one('res.users', u'Diretor Acadêmico',)

    def load_from_openerp7_cron(self):
        """
        Realiza a sincronização dos Campus com o Openerp 7
        :return:
        """
        _logger.info(u'Sincronizando Campus com o Openerp 7')
        import xmlrpclib
        # Conectando ao servidor externo
        server_oe7 = self.env['ud.server.openerp7'].search([('db', '=', 'ud')])
        url, db, username, password = server_oe7.url, server_oe7.db, server_oe7.username, server_oe7.password
        try:
            auth = xmlrpclib.ServerProxy("{}/xmlrpc/common".format(url))
            uid = auth.login(db, username, password)
        except:
            _logger.error(u'Não foi possível conectar-se com o servidor OpenERP 7')
            return
        server = xmlrpclib.ServerProxy("{}/xmlrpc/object".format(url))
        campus_ids = server.execute(db, uid, password, 'ud.campus', 'search', [])
        campus_objs = server.execute_kw(db, uid, password, 'ud.campus', 'read', [campus_ids])

        for campus in campus_objs:
            new_campus = self.search([('name', '=', campus['name'])])
            if not new_campus:
                self.create({
                    'name': campus['name']
                })
