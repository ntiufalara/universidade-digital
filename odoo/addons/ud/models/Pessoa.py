# encoding: UTF-8
from psycopg2._psycopg import IntegrityError

from odoo import models, fields, api
import utils
import logging

_logger = logging.getLogger(__name__)
# http://www.odoo.com/documentation/10.0/reference/mixins.html


class Pessoa(models.Model):
    """
    Classe que representa os campos do formulário Pessoa.
    """
    _name = 'res.users'
    _inherit = 'res.users'

    name = fields.Char(u'Nome completo', required=True)
    cpf = fields.Char(u'CPF', help=u"Entre o CPF no formato: XXX.XXX.XXX-XX")
    rg = fields.Char(u'RG', size=20)
    data_nascimento = fields.Date(u'Data de nascimento')
    genero = fields.Selection(
        [('masculino', u'Masculino'),
         ('feminino', u'Feminino')], u'Gênero'
    )
    estado_civil = fields.Selection(
        [('solteiro', u'Solteiro'), ('casado', u'Casado'), ('viuvo', u'Viúvo'), ('divorciado', u'Divorciado')],
        u'Estado Civil', default='solteiro'
    )
    telefone_fixo = fields.Char(u'Outro telefone')
    celular = fields.Char(u'Telefone principal')
    email = fields.Char(u'E-mail')
    orgaoexpedidor = fields.Char(u'Orgão Expedidor', size=10, help=u"Sigla: Ex. SSP/SP")

    dados = fields.One2many('ud.dados.bancarios', 'pessoa_id', u'Dados Bancários')
    nacionalidade = fields.Selection(utils.NACIONALIDADES, u'Nacionalidade', default='br')
    curriculo_lattes_link = fields.Char(u'Link do Currículo Lattes')
    perfil_ids = fields.One2many('ud.perfil', 'pessoa_id', u'Perfil')
    perfil_principal = fields.Char(u'Perfil', compute="get_perfil")

    endereco_ids = fields.One2many('ud.pessoa.endereco', 'pessoa_id', u'Endereços')
    contato_ids = fields.One2many('ud.pessoa.contato', 'pessoa_id', u'Contatos')

    _sql_constraints = [
        ("ud_cpf_uniq", "unique(cpf)", u'Já existe CPF com esse número cadastrado.'),
        ("ud_rg_uniq", "unique(rg)", u'Já existe RG com esse número cadastrado.'),
    ]

    @api.one
    def get_perfil(self):
        """
        Atribui apenas o nome do primeiro perfil para exibição na lista de pessoas
        :return:
        """
        perfil = None
        for p in self.perfil_ids:
            perfil = p
            break
        self.perfil_principal = perfil.tipo_id.name if perfil else '-'

    @api.model
    def create(self, vals):
        """
        Detemina o login igual ao e-mail
        Adiciona o usuário no grupo "base.usuario_ud"
        :param vals:
        :return:
        """
        if vals.get('email') or vals.get('cpf'):
            vals['login'] = vals['cpf'] or vals['email']
        obj_set = super(models.Model, self).create(vals)
        usuario_ud_group = self.env.ref('base.usuario_ud')
        obj_set.groups_id |= usuario_ud_group
        return obj_set

    def write(self, vals):
        """
        Caso o e-mail seja alterado, altera também o login
        :param vals:
        :return:
        """
        if vals and type(vals) == dict and (vals.get('email') or vals.get('cpf')):
            vals['login'] = vals['cpf'] or vals['email']
        return super(Pessoa, self).write(vals)

    def load_from_openerp7_cron(self):
        """
        Realiza a sincronização das pessoas com o Openerp 7
        :return:
        """
        _logger.info(u'Sincronizando pessoas com o Openerp 7...')
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
        pessoa_ids = server.execute(db, uid, password, 'ud.employee', 'search', [('cpf', '!=', False)])
        pessoas = server.execute_kw(db, uid, password, 'ud.employee', 'read', [pessoa_ids])

        for p in pessoas:
            p = self.clean_openerp7_data(p)
            p_obj = self.search([('cpf', '=', p['cpf']), ('cpf', '!=', False)])
            data = {
                'name': p['resource_id'][1],
                'cpf': p['cpf'],
                'rg': p['rg'],
                'data_nascimento': p['birthday'],
                'genero': p['gender'],
                'estado_civil': p['marital'],
                'telefone_fixo': p['work_phone'],
                'celular': p['mobile_phone'],
                'email': p['work_email'],
                'orgaoexpedidor': p['orgaoexpedidor']
            }
            if not p_obj:
                self.create(data)

    def clean_openerp7_data(self, src_data):
        """
        Remove pontos, traços, virgulas; Substitui valores False por "" (string vazia)
        :param src_data:
        :return:
        """
        if type(src_data) is not dict:
            return
        src_data['cpf'] = src_data['cpf'].replace('.', '').replace('-', '').replace(' ', '') if src_data.get('cpf') else ''
        src_data['mobile_phone'] = src_data['mobile_phone'].replace('(', '').replace(')', '').replace('-', '').replace(' ', '') if src_data.get('mobile_phone') else ''
        src_data['work_phone'] = src_data['work_phone'].replace('(', '').replace(')', '').replace('-', '').replace(' ', '') if src_data.get('work_phone') else ''
        return src_data
