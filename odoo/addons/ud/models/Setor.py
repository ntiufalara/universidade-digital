# encoding: UTF-8
import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class Setor(models.Model):
    """
    Representação do Setor da Universidade
    """
    _name = 'ud.setor'

    name = fields.Char(u'Nome', size=80, required=True)
    descricao = fields.Text(u'Descrição')
    polo_id = fields.Many2one('ud.polo', u'Polo', required=True, ondelete='cascade')
    sigla = fields.Char(u'Sigla', size=50, required=True)
    is_active = fields.Boolean(u'Ativo?', default=True)

    def load_from_openerp7_cron(self):
        """
        Realiza a sincronização dos Setores com o Openerp 7
        :return:
        """
        _logger.info(u'Sincronizando os Setores com o Openerp 7')
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
        setor_ids = server.execute(db, uid, password, 'ud.setor', 'search', [])
        setor_objs = server.execute_kw(db, uid, password, 'ud.setor', 'read', [setor_ids])

        for setor in setor_objs:
            new_setor = self.search([('name', '=', setor['name'])])
            polo_id = self.env['ud.polo'].search([('name', '=', setor['polo_id'][1])])

            # Se polo ainda não existir, pule
            if not polo_id:
                continue

            if not new_setor:
                self.create({
                    'name': setor['name'],
                    'sigla': setor['sigla'],
                    'polo_id': polo_id.id
                })
