# encoding: UTF-8
import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Espaco(models.Model):
    """
    Classe que representa a entidade Espaço.
    """
    _name = 'ud.espaco'

    name = fields.Char(u'Nome', required=True)
    capacidade = fields.Integer(u'Capacidade', required=True, help=u"Número de pessoas.")
    permite_reserva = fields.Boolean(u'Permitir Reserva')
    campus_id = fields.Many2one('ud.campus', u'Campus', required=True)
    polo_id = fields.Many2one('ud.polo', u'Polo', required=True, ondelete='cascade')
    bloco_id = fields.Many2one('ud.bloco', u'Bloco', required=True, ondelete='cascade')
    informacoes_adicionais = fields.Text(u'Descrição')
    responsavel_ids = fields.Many2many('res.users', 'ud_espaco_responsavel', string=u'Responsável')

    @api.onchange('polo_id')
    def limpa_bloco(self):
        """
        Limpa o campo bloco se o polo não pertencer a ele.
        """
        campos = ["bloco_id"]
        valores = {}
        for campo in campos:
            valores[campo] = ""
        return {'value': valores}

    def load_from_openerp7_cron(self):
        """
        Realiza a sincronização dos Espaços com o Openerp 7
        :return:
        """
        _logger.info(u'Sincronizando os espaços com o Openerp 7')
        import xmlrpclib
        # Conectando ao servidor externo
        server_oe7 = self.env['ud.server.openerp7'].search([('db', '=', 'ud')])
        url, db, username, password = server_oe7.url, server_oe7.db, server_oe7.username, server_oe7.password
        try:
            auth = xmlrpclib.ServerProxy("{}/xmlrpc/common".format(url))
            uid = auth.login(db, username, password)
        except:
            _logger.warning(u'Não foi possível se conectar com o seridor Openerp 7')
            return
        server = xmlrpclib.ServerProxy("{}/xmlrpc/object".format(url))
        espaco_ids = server.execute(db, uid, password, 'ud.espaco', 'search', [])
        espaco_objs = server.execute_kw(db, uid, password, 'ud.espaco', 'read', [espaco_ids])

        for espaco in espaco_objs:
            if not espaco['local_polo']:
                _logger.warning(u'O espaço não possui polo associado. Espaço: {}'.format(espaco))
                continue

            polo_id = self.env['ud.polo'].search([('name', '=', espaco['local_polo'][1])])
            # # Se polo ainda não existir, pule
            if not polo_id:
                _logger.warning(u'O polo não foi encontrado: {}'.format(espaco['local_polo']))
                continue
            campus_id = polo_id.campus_id

            # Busca o bloco no banco de dados
            bloco_id = self.env['ud.bloco'].search([('name', '=', espaco['local_bloco_polo'][1])])
            if not bloco_id:
                _logger.warning(u'O bloco não foi encontrado: {}'.format(espaco['local_bloco_polo']))
                continue

            new_espaco = self.search([('name', '=', espaco['name']), ('polo_id', '=', polo_id.id)])
            if not new_espaco:
                self.create({
                    'name': espaco['name'],
                    'polo_id': polo_id.id,
                    'bloco_id': bloco_id.id,
                    'campus_id': campus_id.id,
                    'capacidade': espaco['capacidade'],
                    'permite_reserva': espaco['permite_reserva'],
                    'informacoes_adicionais': espaco['informacoes_adicionais'] if espaco.get(
                        'informacoes_adicionais') else '',

                })
