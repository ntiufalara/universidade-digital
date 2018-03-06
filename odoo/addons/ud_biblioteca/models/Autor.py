# encoding: UTF-8
import logging
from odoo import models, fields
_logger = logging.getLogger(__name__)


class Autor(models.Model):
    """
    Nome: ud.biblioteca.publicacao.autor
    Descrição: Cadastro de autor de publicações
    """
    _name = 'ud.biblioteca.publicacao.autor'

    name = fields.Char(u'Nome', required=True)
    contato = fields.Char(u'E-mail')

    def load_from_openerp7_cron(self):
        """
        Realiza a sincronização das publicações com o Openerp 7
        :return:
        """
        _logger.info(u'Sincronizando autores com o Openerp 7')
        import xmlrpclib
        # Conectando ao servidor externo
        from odoo.addons.ud.models.utils import url, db, username, password
        try:
            auth = xmlrpclib.ServerProxy("{}/xmlrpc/common".format(url))
            uid = auth.login(db, username, password)
        except:
            return
        server = xmlrpclib.ServerProxy("{}/xmlrpc/object".format(url))
        # busca as publicações
        pc_ids = server.execute(db, uid, password, 'ud.biblioteca.publicacao.autor', 'search', [])
        pcs = server.execute_kw(db, uid, password, 'ud.biblioteca.publicacao.autor', 'read', [pc_ids])

        for pc in pcs:
            pc_obj = self.search([('name', '=', pc['name'])])
            if not pc_obj:
                self.create({'name': pc['name']})
