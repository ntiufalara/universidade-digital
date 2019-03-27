# encoding: UTF-8
import logging
from pprint import pprint

from odoo import models, fields

_logger = logging.getLogger(__name__)


class Anexo(models.Model):
    """
    Nome: ud.biblioteca.anexo
    Deescrição: Arquivos contendo as publicações
    """
    _name = 'ud.biblioteca.anexo'

    name = fields.Char(u'Anexo', required=True)
    arquivo = fields.Binary(u'Arquivo PDF')
    exibir_pdf = fields.Boolean(u'Exibir PDF')
    publicacao_id = fields.Many2one('ud.biblioteca.publicacao', u'Publicação')

    def load_from_openerp7_cron(self):
        """
        Realiza a sincronização das publicações com o Openerp 7
        :return:
        """
        _logger.info(u'Sincronizando anexos com o Openerp 7')
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
        # busca os anexos
        anexo_ids = server.execute(db, uid, password, 'ud.biblioteca.anexo', 'search', [('publicacao_id', '!=', False)])

        cont_new = 0
        cont_old = 0
        for anexo_id in anexo_ids:
            anexo_old = server.execute_kw(db, uid, password, 'ud.biblioteca.anexo', 'read', [anexo_id],
                                          {'fields': ['name', 'publicacao_id']})
            anexo_new = self.env['ud.biblioteca.anexo'].search([('name', '=', anexo_old['name'])])
            if not anexo_new:
                cont_new += 1
                _logger.info(u'Anexo ainda não cadastrado... {}'.format(anexo_old['publicacao_id'][1]))
                anexo_old = server.execute_kw(db, uid, password, 'ud.biblioteca.anexo', 'read', [anexo_id])
                publicacao = self.env['ud.biblioteca.publicacao'].search([('name', '=', anexo_old['publicacao_id'][1])])
                pprint(publicacao)
                self.create({
                    'name': anexo_old['name'],
                    'arquivo': anexo_old['arquivo'],
                    'publicacao_id': publicacao.id
                })
            else:
                cont_old += 1
                _logger.info(u'Anexo já cadastrado: {}'.format(anexo_old['publicacao_id'][1]))
        _logger.info(u'Total: {}'.format(len(anexo_ids)))
        _logger.info(u'Arquivos criados: {}'.format(cont_new))
        _logger.info(u'Arquivos já existentes: {}'.format(cont_old))
