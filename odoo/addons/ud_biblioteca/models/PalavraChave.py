# encoding: UTF-8
import logging
from odoo import models, fields
_logger = logging.getLogger(__name__)


class PalavraChave(models.Model):
    """
    Nome: ud.biblioteca.p_chave
    Descrição: Armazenar as palavras-chave de cada publicação
    """
    _name = 'ud.biblioteca.p_chave'

    name = fields.Char('Palavra-chave', required=True)
    publicacao_id = fields.Many2many('ud.biblioteca.publicacao', 'publicacao_p_chave_rel', string=u'Palavras-chave',
                                     ondelete='set null')

    _sql_constraints = [
        ('name_uniq', 'unique(name)', u'Já existe uma palavra-chave de mesmo nome')
    ]

    def load_from_openerp7_cron(self):
        """
        Realiza a sincronização das palavras-chave com o Openerp 7
        :return:
        """
        _logger.info(u'Sincronizando palavras-chave com o Openerp 7')
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
        pc_ids = server.execute(db, uid, password, 'ud.biblioteca.pc', 'search', [])
        pcs = server.execute_kw(db, uid, password, 'ud.biblioteca.pc', 'read', [pc_ids])

        for pc in pcs:
            pc_obj = self.search([('name', '=', pc['name'])])
            if not pc_obj:
                self.create({'name': pc['name']})
