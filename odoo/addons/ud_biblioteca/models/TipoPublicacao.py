# encoding: UTF-8
import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)


class TipoPublicacao(models.Model):
    """
    Nome: ud.biblioteca.publicacao.tipo
    Descrição: Cadastro de tipos de publicações
    """
    _name = 'ud.biblioteca.publicacao.tipo'
    _description = 'Tipo de publicação'

    name = fields.Char(u'Tipo', required=True)

    def load_from_openerp7_cron(self):
        """
        Realiza a sincronização dos Tipos de publicação com o Openerp 7
        :return:
        """
        _logger.info(u'Sincronizando Tipos de publicação com o Openerp 7')
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
        # busca as publicações
        tipo_ids = server.execute(db, uid, password, 'ud.biblioteca.publicacao.tipo', 'search', [])
        tipos = server.execute_kw(db, uid, password, 'ud.biblioteca.publicacao.tipo', 'read', [tipo_ids])

        for tipo in tipos:
            new_tipo_obj = self.search([('name', '=', tipo['name'])])
            if not new_tipo_obj:
                self.create({'name': tipo['name']})
