# encoding: UTF-8
import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class Bloco(models.Model):
    """
    Representação do Bloco (local dentro do polo)
    """
    _name = 'ud.bloco'
    _description = u'Bloco'

    _order = "name"

    name = fields.Char(u'Bloco', size=80, required=True)
    polo_id = fields.Many2one('ud.polo', u'Polo', ondelete='cascade', invisible=True)
    campus_id = fields.Char(related='polo_id.campus_id.name', string=u'Campus')

    def load_from_openerp7_cron(self):
        """
        Realiza a sincronização dos Blocos com o Openerp 7
        :return:
        """
        _logger.info(u'Sincronizando os blocos com o Openerp 7')
        import xmlrpclib
        # Conectando ao servidor externo
        server_oe7 = self.env['ud.server.openerp7'].search([('db', '=', 'ud')])
        url, db, username, password = server_oe7.url, server_oe7.db, server_oe7.username, server_oe7.password
        try:
            auth = xmlrpclib.ServerProxy("{}/xmlrpc/common".format(url))
            uid = auth.login(db, username, password)
        except:
            _logger.warning(u'Não foi possível conectar com o servidor Openerp 7')
            return
        server = xmlrpclib.ServerProxy("{}/xmlrpc/object".format(url))
        bloco_ids = server.execute(db, uid, password, 'ud.bloco', 'search', [])
        bloco_objs = server.execute_kw(db, uid, password, 'ud.bloco', 'read', [bloco_ids])

        for bloco in bloco_objs:
            new_bloco = self.search([('name', '=', bloco['name'])])
            if not bloco['ud_bloco_ids']:
                _logger.warning(u'O bloco não possui polo associado. Bloco: {}'.format(bloco))
                continue
            polo_id = self.env['ud.polo'].search([('name', '=', bloco['ud_bloco_ids'][1])])

            # Se polo ainda não existir, pule
            if not polo_id:
                _logger.warning(u'Não foi possível encontrar o polo: {}'.format(
                    bloco['ud_bloco_ids']
                ))
                continue

            if not new_bloco:
                self.create({
                    'name': bloco['name'],
                    'polo_id': polo_id.id
                })

