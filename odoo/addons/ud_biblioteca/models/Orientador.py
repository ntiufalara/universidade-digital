# encoding: UTF-8
import logging
from odoo import models, fields, api
_logger = logging.getLogger(__name__)


class Orientador(models.Model):
    """
    Nome: ud.biblioteca.orientador
    Deescrição: Relação many2many de publicação para orientador, permite adicionar mais de um orientador
    """
    _name = 'ud.biblioteca.publicacao.orientador'
    _description = 'Orientador'

    # Nome preenchido pelo usuário
    name = fields.Char(u'Nome', required=True)
    ultimo_nome = fields.Char(u'Ultimo nome', required=True)
    # Nome de exibição
    display_name = fields.Char(u'Nome', compute='get_name')
    titulacao_id = fields.Many2one('ud.biblioteca.orientador.titulacao', u'Titulação')
    publicacao_orientador_ids = fields.Many2many('ud.biblioteca.publicacao', 'publicacao_orientador_rel',
                                                 string=u'Orientador em')
    publicacao_coorientador_ids = fields.Many2many('ud.biblioteca.publicacao', 'publicacao_coorientador_rel',
                                                   string=u'Coorientador em')

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, record.display_name))
        return result

    @api.depends('name', 'ultimo_nome', 'titulacao_id')
    @api.one
    def get_name(self):
        if self.titulacao_id:
            self.display_name = u"{}. {}, {}".format(
                self.titulacao_id.sigla,
                self.ultimo_nome,
                self.name
            )
        else:
            self.display_name = u"{}, {}".format(
                self.ultimo_nome,
                self.name
            )

    def load_from_openerp7_cron(self):
        """
        Realiza a sincronização das publicações com o Openerp 7
        :return:
        """
        _logger.info(u'Sincronizando orientadores com o Openerp 7')
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
        orientador_ids = server.execute(db, uid, password, 'ud.biblioteca.orientador', 'search', [])
        orientadores = server.execute_kw(db, uid, password, 'ud.biblioteca.orientador', 'read', [orientador_ids])

        for orientador in orientadores:
            titulacao_obj = None
            if orientador.get('titulacao_id'):
                titulacao_obj = self.env['ud.biblioteca.orientador.titulacao'].search([('name', '=', orientador.get('titulacao_id')[1])])
            if orientador.get('titulacao_id') and not titulacao_obj:
                continue
            orientador_obj = self.search([('name', '=', orientador['name'])])
            if not orientador_obj:
                self.create({'name': orientador['name']})