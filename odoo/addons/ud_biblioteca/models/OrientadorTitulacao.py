# encoding: UTF-8
import logging
from odoo import models, fields
_logger = logging.getLogger(__name__)


class OrientadorTitulacao(models.Model):
    """
    Nome: ud.biblioteca.orientador.titulacao
    Descrição: Relação Many2many de orientador para titulação, permite adicionar mais de uma titulação
    """
    _name = 'ud.biblioteca.orientador.titulacao'

    name = fields.Char(u"Nome", required=True)
    sigla = fields.Char(u'Sigla', required=True)
    orientador_ids = fields.One2many('ud.biblioteca.publicacao.orientador', 'titulacao_id', u'Orientadores')

    def load_from_openerp7_cron(self):
        """
        Realiza a sincronização das titulações com o Openerp 7
        :return:
        """
        _logger.info(u'Sincronizando orientador.titulacao com o Openerp 7')
        import xmlrpclib
        # Conectando ao servidor externo
        server_oe7 = self.env['ud.server.openerp7'].search([('db', '=', 'ud')])
        url, db, username, password = server_oe7.url, server_oe7.db, server_oe7.username, server_oe7.password
        try:
            auth = xmlrpclib.ServerProxy("{}/xmlrpc/common".format(url))
            uid = auth.login(db, username, password)
        except:
            _logger.error(u'A conexão com o servidor Openerp7 não foi bem sucedida')
            return
        server = xmlrpclib.ServerProxy("{}/xmlrpc/object".format(url))
        # busca as publicações
        titulacao_ids = server.execute(db, uid, password, 'ud.biblioteca.orientador.titulacao', 'search', [])
        titulacoes = server.execute_kw(db, uid, password, 'ud.biblioteca.orientador.titulacao', 'read', [titulacao_ids])

        for titulacao in titulacoes:
            titulacao_obj = self.search([('name', '=', titulacao['name'])])
            if not titulacao_obj:
                self.create({'name': titulacao['name'], 'sigla': titulacao['name']})
