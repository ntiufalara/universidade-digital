# encoding: UTF-8
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Autor(models.Model):
    """
    Nome: ud.biblioteca.publicacao.autor
    Descrição: Cadastro de autor de publicações
    """
    _name = 'ud.biblioteca.publicacao.autor'
    _description = 'Autor'
    _rec_name = 'display_name'

    display_name = fields.Char(u'Nome', compute='get_name')
    name = fields.Char(u'Nome', required=True)
    ultimo_nome = fields.Char(u'Último nome', required=True)
    contato = fields.Char(u'E-mail')

    @api.one
    def get_name(self):
        """
        Exibe o nome do autor no formato NBR
        :return:
        """
        self.display_name = u"{}, {}".format(self.ultimo_nome, self.name)

    def load_from_openerp7_cron(self):
        """
        Realiza a sincronização das publicações com o Openerp 7
        :return:
        """
        _logger.info(u'Sincronizando autores com o Openerp 7')
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
        pc_ids = server.execute(db, uid, password, 'ud.biblioteca.publicacao.autor', 'search', [])
        pcs = server.execute_kw(db, uid, password, 'ud.biblioteca.publicacao.autor', 'read', [pc_ids])

        for pc in pcs:
            pc_obj = self.search([('name', '=', pc['name'])])
            if not pc_obj:
                self.create({'name': pc['name']})
