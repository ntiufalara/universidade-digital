# encoding: UTF-8
import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class Polo(models.Model):
    """
    Representação do Polo (local)
    """
    _name = 'ud.polo'

    name = fields.Char(u'Nome', required=True, help=u"Ex.: Viçosa, Penedo, Palmeira etc.")
    campus_id = fields.Many2one('ud.campus', u'Campus', required=True)
    localizacao = fields.Char(u'Endereço', size=120)
    is_active = fields.Boolean(u'Ativo?', default=True)
    descricao = fields.Text(u'Descrição')
    bloco_ids = fields.One2many('ud.bloco', 'polo_id', u'Bloco')

    def load_from_openerp7_cron(self):
        """
        Realiza a sincronização dos Polos com o Openerp 7
        :return:
        """
        _logger.info(u'Sincronizando os Polos com o Openerp 7')
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
        polo_ids = server.execute(db, uid, password, 'ud.polo', 'search', [])
        polo_objs = server.execute_kw(db, uid, password, 'ud.polo', 'read', [polo_ids])

        for polo in polo_objs:
            new_polo = self.search([('name', '=', polo['name'])])
            campus_id = self.env['ud.campus'].search([('name', '=', polo['campus_id'][1])])
            # Se campus ainda não existir, pule
            if not campus_id:
                continue

            if not new_polo:
                self.create({
                    'name': polo['name'],
                    'campus_id': campus_id.id
                })

