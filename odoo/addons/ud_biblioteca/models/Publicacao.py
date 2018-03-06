# encoding: UTF-8
import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Publicacao(models.Model):
    """
    Nome: ud.biblioteca.publicacao
    Descrição: Cadastro de publicações do repositório institucional
    """
    _name = 'ud.biblioteca.publicacao'

    __polo_id = 0

    _order = "create_date desc"

    name = fields.Char(u'Título', required=True)
    autor_id = fields.Many2one('ud.biblioteca.publicacao.autor', u'Autor', required=True)
    nome_autor = fields.Char(related='autor_id.name', string=u"Nome do autor")
    contato = fields.Char(related='autor_id.contato', string=u"E-mail para contato")
    ano_pub = fields.Char(u'Ano de publicação', required=True)
    campus_id = fields.Many2one("ud.campus", u"Campus", required=True, ondelete='set null',
                                default=lambda self: self.busca_campus())
    curso_id = fields.Many2one('ud.curso', u'Curso', ondelete='set null')
    curso_indefinido = fields.Boolean(u"Outro curso")
    curso_indefinido_detalhes = fields.Char(u"Curso")
    palavras_chave_ids = fields.Many2many('ud.biblioteca.p_chave', 'publicacao_p_chave_rel', string=u'Palavras-chave',
                                          required=True)
    polo_id = fields.Many2one('ud.polo', u'Polo', required=True, default=lambda self: self.busca_polo())
    orientador_ids = fields.Many2many('ud.biblioteca.publicacao.orientador', 'publicacao_orientador_rel',
                                      string=u'Orientadores', required=True)
    coorientador_ids = fields.Many2many('ud.biblioteca.publicacao.orientador', 'publicacao_coorientador_rel',
                                        string='Coorientadores')
    anexo_ids = fields.One2many('ud.biblioteca.anexo', 'publicacao_id', u'Anexos em PDF')
    categoria_cnpq_id = fields.Many2one('ud.biblioteca.publicacao.categoria_cnpq', u'Categoria CNPQ')
    tipo_id = fields.Many2one('ud.biblioteca.publicacao.tipo', u"Tipo", required=True)
    autorizar_publicacao = fields.Boolean(u"Autorizar publicação")
    visualizacoes = fields.Integer(u'Visualizações', required=True, default=0)
    area_ids = fields.Many2many('ud.biblioteca.publicacao.area', 'area_publicacao_real',
                                string=u'Áreas do trabalho')

    def read(self, fields=None, load='_classic_read'):
        """
        Cria um contador de leituras para a publicação
        :param fields:
        :param load:
        :return:
        """
        result = super(Publicacao, self).read(fields, load)
        if not fields:
            fields = []
        if len(self) == 1 and u'__last_update' in fields:
            if self.visualizacoes is not None:
                self.sudo().visualizacoes = self.sudo().visualizacoes + 1
        return result

    @api.model
    def create(self, vals):
        # Recupera o polo para salvar
        if self.__polo_id != 0 and not vals.get('polo_id'):
            vals['polo_id'] = self.__polo_id

        # Salvando contato do autor
        self.env['ud.biblioteca.publicacao.autor'].browse(vals.get('autor_id')).write({'contato': vals.get('contato')})
        return super(Publicacao, self).create(vals)

    @api.onchange('polo_id')
    def onchange_polo_id(self):
        """
        Salva o polo para criação posterior
        Fields disabled não são enviados ao servidor
        :return:
        """
        self.__polo_id = self.polo_id

    @api.model
    def busca_campus(self):
        """
        Busca o campus ao qual o usuário está responsável
        :return: Retorna o id do campus
        """
        responsavel_objs = self.env['ud.biblioteca.responsavel'].sudo().search([('pessoa_id', '=', self.env.uid)])
        # O for é para iteração do recordset
        for obj in responsavel_objs:
            # Interessa apenas o primeiro registro na lista
            return obj.campus_id.id

    @api.model
    def busca_polo(self):
        """
        Busca o polo ao qual o usuário está responsável
        Caso o usuário seja o administrador do campus, returna None
        :return:
        """
        responsavel_objs = self.env['ud.biblioteca.responsavel'].sudo().search([('pessoa_id', '=', self.env.uid)])
        # O for é para iteração do recordset
        for obj in responsavel_objs:
            # Caso ele seja admin do campus, retorna None
            if obj.admin_campus:
                return None
            return obj.polo_id.id

    def load_from_openerp7_cron(self):
        """
        Realiza a sincronização das publicações com o Openerp 7
        :return:
        """
        _logger.info(u'Sincronizando publicações com o Openerp 7')
        import xmlrpclib
        # Conectando ao servidor externo
        from odoo.addons.ud.models.utils import url, db, username, password
        try:
            auth = xmlrpclib.ServerProxy("{}/xmlrpc/common".format(url))
            uid = auth.login(db, username, password)
        except:
            # Se não conectar, saia da função
            return
        server = xmlrpclib.ServerProxy("{}/xmlrpc/object".format(url))
        # busca as publicações
        pub_ids = server.execute(db, uid, password, 'ud.biblioteca.publicacao', 'search', [])
        pubs = server.execute_kw(db, uid, password, 'ud.biblioteca.publicacao', 'read', [pub_ids])

        # busca os campos relacionais e cria nova publicacao se necessário
        for pub in pubs:
            pub_obj = self.search([('name', '=', pub['name'])])
            if not pub_obj:
                p_chave_old = server.execute_kw(db, uid, password, 'ud.biblioteca.pc', 'read',
                                                [pub['palavras_chave_ids']])
                p_chave_old_names = [p['name'] for p in p_chave_old]
                p_chave = self.env['ud.biblioteca.p_chave'].search([('name', 'in', p_chave_old_names)])
                # Caso nem todas as palavras-chave estejam no banco, pula
                if len(p_chave) != len(p_chave_old_names):
                    continue
                # Orientadores
                orientadores_old = server.execute_kw(db, uid, password, 'ud.biblioteca.orientador', 'read',
                                                     [pub['orientador_ids']])
                orientadores_old_names = [o['name'] for o in orientadores_old]
                orientadores = self.env['ud.biblioteca.publicacao.orientador'].search(
                    [('nome_orientador', 'in', orientadores_old_names)]
                )
                # Caso nem todas os orientadores estejam no banco, pula
                if len(orientadores) != len(orientadores_old_names):
                    continue
                # Coorientadores
                coorientadores_old = server.execute_kw(db, uid, password, 'ud.biblioteca.orientador', 'read',
                                                       [pub['coorientador_ids']])
                coorientadores_old_names = [o['name'] for o in coorientadores_old]
                coorientadores = self.env['ud.biblioteca.publicacao.orientador'].search(
                    [('nome_orientador', 'in', coorientadores_old_names)]
                )
                # Caso nem todas os orientadores estejam no banco, pula
                if len(coorientadores) != len(coorientadores_old_names):
                    continue
                # Campus, polo e curso
                campus = self.env['ud.campus'].search([('name', '=', pub['ud_campus_id'][1])])
                polo = self.env['ud.polo'].search([('name', '=', pub['polo_id'][1])])
                curso = self.env['ud.curso'].search([('name', '=', pub['curso'][1])])
                # tipo de publicação
                tipo = self.env['ud.biblioteca.publicacao.tipo'].search([('name', '=', pub['tipo_id'][1])])
                # Caso não corresponda, pula
                if not tipo:
                    continue
                # autor
                autor = self.env['ud.biblioteca.publicacao.autor'].search([('name', '=', pub['autor_id'][1])])
                # Caso nem todas os orientadores estejam no banco, pula
                if not autor:
                    continue
                obj = self.create({
                    'name': pub['name'],
                    'campus_id': campus.id,
                    'polo_id': polo.id,
                    'curso_id': curso.id,
                    'tipo_id': tipo.id,
                    'autor_id': autor.id,
                    'ano_pub': pub['ano_pub'],
                    'autorizar_publicacao': pub['autorizar_publicacao'],
                })
                obj.orientador_ids |= orientadores
                obj.coorientador_ids |= coorientadores
                obj.palavras_chave_ids |= p_chave
