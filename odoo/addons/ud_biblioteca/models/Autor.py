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

    _order = 'name asc'

    display_name = fields.Char(u'Nome', compute='get_name', stored=True)
    name = fields.Char(u'Nome', required=True)
    ultimo_nome = fields.Char(u'Último nome', required=True)
    contato = fields.Char(u'E-mail')

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, record.display_name))
        return result

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
            _logger.error(u'A conexão com o servidor Openerp7 não foi bem sucedida')
            return
        server = xmlrpclib.ServerProxy("{}/xmlrpc/object".format(url))
        # busca as publicações
        autor_ids = server.execute(db, uid, password, 'ud.biblioteca.publicacao.autor', 'search', [])
        autores = server.execute_kw(db, uid, password, 'ud.biblioteca.publicacao.autor', 'read', [autor_ids])

        for autor in autores:
            try:
                full_name = autor['name'].split(',')
                name = full_name[1].strip()
                ultimo_nome = full_name[0]
            except IndexError:
                _logger.error(u'O autor: {}, não pode ser salvo'.format(autor['name']))
                continue

            autor_obj = self.search([('name', '=', name), ('ultimo_nome', '=', ultimo_nome)])
            # Separa os nomes juntos em "primeiro nome" e "último nome"
            if not autor_obj:
                try:
                    data = {
                        'name': name,
                        'ultimo_nome': ultimo_nome,
                    }
                    self.create(data)
                except IndexError:
                    _logger.error(u'O autor: {}, não pode ser salvo'.format(autor['name']))
                    continue
