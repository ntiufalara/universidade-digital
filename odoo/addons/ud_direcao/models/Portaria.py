# encoding: UTF-8
import logging
from odoo import models, fields, api
_logger = logging.getLogger(__name__)


class Portaria(models.Model):
    """
    Representa um documento (Portaria) emitido por algum setor dentro da universidade
    """
    _name = 'ud.direcao.portaria'

    _rec_name = 'nro_portaria'

    nro_portaria = fields.Char(u'Número', required=True)
    descricao = fields.Text(u'Descrição', required=True)
    data = fields.Date('Data', required=True)
    file_name = fields.Char('Nome do arquivo', )
    anexo = fields.Binary('Anexo', required=True)
    campus_id = fields.Many2one('ud.campus', "Campus", required=True)
    polo_id = fields.Many2one('ud.polo', 'Polo', required=True, domain="[('campus_id', '=', campus_id)]")
    setor_id = fields.Many2one('ud.setor', 'Emissor', required=True,
                               domain="[('polo_id', '=', polo_id), ('emite_portaria', '=', True)]")
    responsavel_id = fields.Many2one('res.users', u'Responsável', readonly=True, related='setor_id.responsavel_id')
    setor_destino_id = fields.Many2one('ud.setor', "Destino", required=False, domain="[('polo_id', '=', polo_id)]")

    def load_from_openerp7_cron(self):
        """
        Realiza a sincronização das portarias com o Openerp 7
        :return:
        """
        _logger.info(u'Sincronizando portarias com o Openerp 7')
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
        portaria_ids = server.execute(db, uid, password, 'ud.direcao.portaria', 'search', [])
        portarias = server.execute_kw(db, uid, password, 'ud.direcao.portaria', 'read', [portaria_ids])

        for portaria in portarias:
            portaria_obj = self.search([('nro_portaria', '=', portaria['nro_portaria'])])
            if not portaria_obj:
                campus = self.env['ud.campus'].search([('name', '=', portaria['campus_id'][1])])
                polo = self.env['ud.polo'].search([('name', '=', portaria['polo_id'][1])])
                setor = self.env['ud.setor'].search([('name', '=', portaria['setor_id'][1])])
                setor_destino = self.env['ud.setor'].search([('name', '=', portaria['setor_destino_id'][1])])
                responsavel = self.env['res.users'].search([('name', '=', portaria['responsavel_id'][1])])
                self.create({
                    'nro_portaria': portaria['nro_portaria'],
                    'descricao': portaria['descricao'],
                    'data': portaria['data'],
                    'file_name': portaria['file_name'],
                    'anexo': portaria['anexo'],
                    'campus_id': campus.id,
                    'polo_id': polo.id,
                    'setor_id': setor.id,
                    'responsavel_id': responsavel.id,
                    'setor_destino_id': setor_destino.id
                })
