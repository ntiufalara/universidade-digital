# encoding: UTF-8
import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Responsavel(models.Model):
    _name = 'ud.biblioteca.responsavel'

    name = fields.Char(u'Nome', compute='get_name')
    pessoa_id = fields.Many2one('res.users', u'Pessoa', required=True)
    campus_id = fields.Many2one('ud.campus', u'Campus', required=True)
    admin_campus = fields.Boolean(u'Administrador do campus')
    polo_id = fields.Many2one('ud.polo', u'Polo', required=False)

    _sql_constraints = [
        ('pessoa_id_uniq', 'unique(pessoa_id)',
         "Encontramos outro registro para a mesma pessoa, por favor edite ou apague o outro registro pra salvar.")
    ]

    @api.one
    @api.depends('campus_id', 'pessoa_id', 'polo_id')
    def get_name(self):
        polo_name = "--" if not self.polo_id.name else self.polo_id.name
        self.name = u"{}; Campus: {}; Polo: {}".format(self.pessoa_id.name, self.campus_id.name, polo_name)

    @api.model
    def create(self, vals):
        res = super(Responsavel, self).create(vals)
        group_gerente_servico = self.env.ref('ud_biblioteca.group_biblioteca_bibliotecario')
        res.pessoa_id.groups_id |= group_gerente_servico
        return res

    def load_from_openerp7_cron(self):
        """
        Realiza a sincronização dos Responsáveis por publicação com o Openerp 7
        :return:
        """
        _logger.info(u'Sincronizando Responsáveis (Biblioteca) com o Openerp 7')
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
        responsavel_ids = server.execute(db, uid, password, 'ud.biblioteca.responsavel', 'search', [])
        responsaveis = server.execute_kw(db, uid, password, 'ud.biblioteca.responsavel', 'read', [responsavel_ids])

        for responsavel in responsaveis:
            new_responsavel = self.search([('pessoa_id.name', '=', responsavel['employee_id'][1])])
            if not new_responsavel:
                admin_campus = responsavel['admin_campus'] or False
                pessoa = self.env['res.users'].search([('name', '=', responsavel['employee_id'][1])])
                if not pessoa:
                    _logger.error(u'Não foi possível encontrar a Pessoa: {}'.format(responsavel['employee_id'][1]))
                    continue
                campus = self.env['ud.campus'].search([('name', '=', responsavel['campus_id'][1])])
                if not campus:
                    _logger.error(u'Não foi possível encontrar o Campus: {}'.format(responsavel['campus_id'][1]))
                    continue
                polo = False
                if responsavel.get('polo_id'):
                    polo = self.env['ud.polo'].search([('name', '=', responsavel['polo_id'][1])])
                    if not polo:
                        _logger.error(u'Não foi possível encontrar o Polo: {}'.format(responsavel['polo_id'][1]))
                        continue
                self.create({
                    'name': responsavel['name'],
                    'campus_id': campus.id,
                    'polo_id': polo.id if polo else False ,
                    'pessoa_id': pessoa.id,
                    'admin_campus': admin_campus
                })
