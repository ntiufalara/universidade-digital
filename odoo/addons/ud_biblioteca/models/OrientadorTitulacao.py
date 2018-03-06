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
        Realiza a sincronização das publicações com o Openerp 7
        :return:
        """
        _logger.info(u'Sincronizando orientador.titulacao com o Openerp 7')
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
        titulacao_ids = server.execute(db, uid, password, 'ud.biblioteca.pc', 'search', [])
        titulacoes = server.execute_kw(db, uid, password, 'ud.biblioteca.pc', 'read', [titulacao_ids])

        for titulacao in titulacoes:
            titulacao_obj = self.search([('name', '=', titulacao['name'])])
            if not titulacao_obj:
                self.create({'name': titulacao['name'], 'sigla': 'Id'})
