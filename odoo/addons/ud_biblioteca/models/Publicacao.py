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

    _order = "ano_pub desc"

    name = fields.Char(u'Título', required=True)
    # autor_id = fields.Many2one('ud.biblioteca.publicacao.autor', u'Autor', required=False)
    autor_ids = fields.Many2many('ud.biblioteca.publicacao.autor', 'ud_biblioteca_publicacao_autores', 'pub_id',
                                 'autor_id', u'Autores')
    ano_pub = fields.Char(u'Ano de publicação', required=True)
    campus_id = fields.Many2one("ud.campus", u"Campus", required=True, ondelete='set null',
                                default=lambda self: self.busca_campus())
    curso_id = fields.Many2one('ud.curso', u'Curso', ondelete='set null')
    curso_indefinido = fields.Boolean(u"Outro curso")
    curso_indefinido_detalhes = fields.Char(u"Curso")
    observacoes = fields.Text(u'Observações')
    palavras_chave_ids = fields.Many2many('ud.biblioteca.p_chave', 'publicacao_p_chave_rel', string=u'Palavras-chave',
                                          required=True)
    polo_id = fields.Many2one('ud.polo', u'Polo', required=True, default=lambda self: self.busca_polo())
    # usado para recuperar o polo ao criar
    polo_txt = fields.Char(u'Polo id')

    orientador_ids = fields.Many2many('ud.biblioteca.publicacao.orientador', 'publicacao_orientador_rel',
                                      string=u'Orientadores', required=False)
    orientadores_txt = fields.Char(u'Orientadores')
    coorientador_ids = fields.Many2many('ud.biblioteca.publicacao.orientador', 'publicacao_coorientador_rel',
                                        string='Coorientadores')
    coorientadores_txt = fields.Char(u'Coorientadores')
    anexo_ids = fields.One2many('ud.biblioteca.anexo', 'publicacao_id', u'Anexos em PDF')
    categoria_cnpq_id = fields.Many2many('ud.biblioteca.publicacao.categoria_cnpq', 'categoria_cnpq_ids',
                                         string=u'Categoria CNPQ')
    tipo_id = fields.Many2one('ud.biblioteca.publicacao.tipo', u"Tipo", required=True)
    autorizar_publicacao = fields.Boolean(u"Não embargado")
    visualizacoes = fields.Integer(u'Visualizações', required=True, default=0)
    area_ids = fields.Many2many('ud.biblioteca.publicacao.area', 'area_publicacao_real',
                                string=u'Áreas do conhecimento/Localização')
    bibliotecario_responsavel = fields.Many2one('ud.biblioteca.responsavel', u'Bibliotecário', required=False,
                                                default=lambda self: self.get_bibliotecario())
    resumo = fields.Html(u'Resumo')
    titulo_abstract = fields.Char(u'Título', default="Abstract")
    abstract = fields.Html(u'Abstract', required=False)
    create_date = fields.Datetime(u'Data de inclusão')
    pessoas_notificadas = fields.Boolean(u'Notificações enviadas?')

    def name_get(self):
        """
        Com nomes muito grandes, mostra apenas uma versão resumida
        :return:
        """
        result = super(Publicacao, self).name_get()
        result_list = []
        slice_len = 50
        for obj in result:
            obj_list = list(obj)
            if len(obj_list[1]) > slice_len:
                obj_list[1] = u'{}...'.format(obj_list[1][:slice_len])
            result_list.append(obj_list)
        return result_list

    @api.model
    def get_bibliotecario(self):
        for resp in self.env.user.biblioteca_responsavel_ids:
            return resp.id

    def visualizacoes_totais(self):
        """
        Retorna a quantidade de visualizações de todas as publicações do repositório
        :return:
        """
        self.env.cr.execute('''
            SELECT SUM(visualizacoes) FROM ud_biblioteca_publicacao;
        ''')
        result = self.env.cr.fetchall()
        try:
            result = result[0][0]
        except IndexError:
            result = 0
        return result

    @api.one
    def visualizacoes_plus(self):
        self.sudo().visualizacoes = self.sudo().visualizacoes + 1

    @api.model
    def create(self, vals):
        obj = super(Publicacao, self).create(vals)
        self.notifica_interessados(obj)
        return obj

    def notifica_interessados(self, obj):
        """
        Envia e-mail notificando autores, orientadores e coorientadores ao criar uma nova publicação
        :param obj:
        :return:
        """
        mail = self.env['mail.mail']

        template_html = '''
        <img height="37px" width="140px" style="display:block" alt="Logo UD" title="Logo UD" 
        src="https://i.ibb.co/8DBzkj9/logo-ud-svg.png"/>
        <p>Olá,<br/><br/>
        Você foi adicionado como {tipo} em uma publicação cadastrada no Repositório da Biblioteca Campus 
        Arapiraca<br/><br/>
        Para ver a publicação, acesse o link: <a href="{link}">{link}</a>
        
        <!--
        Logo RI
        <img src="https://i.ibb.co/KxDKTfp/logo-bca-svg.png" alt="logo-bca-svg" border="0"></a>
        Logo BCA
        <a href="https://imgbb.com/"><img src="https://i.ibb.co/47W45RD/logo-biblioteca-ufal-svg.png" alt="logo-biblioteca-ufal-svg" border="0"></a>
        -->
        '''

        template_data = {
            'subject': 'Nova publicação cadastrada.',
            'email_from': 'universidade.digital.notify@gmail.com',
            'auto_delete': True,
        }

        emails = [autor.contato for autor in obj.autor_ids if autor.contato]
        template_data['body_html'] = template_html.format(**{
            'tipo': 'autor',
            'link': 'https://ud10.arapiraca.ufal.br/repositorio/publicacoes/' + str(obj.id),
        })
        template_data['email_to'] = ', '.join(emails)
        m = mail.create(template_data)
        m.send()

        emails = [orientador.contato for orientador in obj.orientador_ids if orientador.contato]
        template_data['body_html'] = template_html.format(**{
            'tipo': 'orientador',
            'link': 'https://ud10.arapiraca.ufal.br/repositorio/publicacoes/' + str(obj.id),
        })
        template_data['email_to'] = ', '.join(emails)
        m = mail.create(template_data)
        m.send()

        emails = [coorientador.contato for coorientador in obj.coorientador_ids if coorientador.contato]
        template_data['body_html'] = template_html.format(**{
            'tipo': 'coorientador',
            'link': 'https://ud10.arapiraca.ufal.br/repositorio/publicacoes/' + str(obj.id),
        })
        template_data['email_to'] = ', '.join(emails)
        m = mail.create(template_data)
        m.send()

        # Marca como notificado
        obj.pessoas_notificadas = True

    @api.onchange('polo_id')
    def onchange_polo_id(self):
        """
        Salva o polo para criação posterior
        Fields disabled não são enviados ao servidor
        :return:
        """
        self.___polo_id = self.polo_id.id

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
        server_oe7 = self.env['ud.server.openerp7'].search([('db', '=', 'ud')])
        url, db, username, password = server_oe7.url, server_oe7.db, server_oe7.username, server_oe7.password
        try:
            auth = xmlrpclib.ServerProxy("{}/xmlrpc/common".format(url))
            uid = auth.login(db, username, password)
        except:
            # Se não conectar, saia da função
            _logger.error(u'A conexão com o servidor Openerp7 não foi bem sucedida')
            return
        server = xmlrpclib.ServerProxy("{}/xmlrpc/object".format(url))
        # busca as publicações
        pub_ids = server.execute(db, uid, password, 'ud.biblioteca.publicacao', 'search', [])
        pubs = server.execute_kw(db, uid, password, 'ud.biblioteca.publicacao', 'read', [pub_ids])

        # busca os campos relacionais e cria nova publicacao se necessário
        cont = 0
        for pub in pubs:
            pub_obj = self.search([('name', '=', pub['name'])])
            if not pub_obj:
                p_chave = pub.get('palavras_chave_ids')
                if not p_chave:
                    p_chave = pub.get('palavras-chave_ids')

                # Pula publicações sem palavras-chave, sem orientadores
                if not p_chave:
                    _logger.warning(u'Palavra-chave não encontrada: {}'.format(pub['name']))
                    continue
                if not pub['orientador_ids']:
                    _logger.warning(u'Orientadores não encontrados: {}'.format(pub['name']))
                    continue
                p_chave_old = server.execute_kw(db, uid, password, 'ud.biblioteca.pc', 'read',
                                                [p_chave])
                p_chave_old_names = [p['name'] for p in p_chave_old]
                p_chave = self.env['ud.biblioteca.p_chave'].search([('name', 'in', p_chave_old_names)])
                # Caso nem todas as palavras-chave estejam no banco, pula
                if len(p_chave) != len(p_chave_old_names):
                    _logger.error(
                        u'Nem todas as palavras-chave desta publicação estão cadastradas. Publicação: {}'.format(
                            pub['name']
                        )
                    )
                    continue
                # Orientadores
                orientadores_old = server.execute_kw(db, uid, password, 'ud.biblioteca.orientador', 'read',
                                                     [pub['orientador_ids']])
                # Cria uma lista de "primeiros_nomes" e outra de "ultimos_nomes"
                orientadores_old_names = []
                orientadores_old_ultimos_nomes = []
                for o in orientadores_old:
                    full_name = o['name'].split(',')
                    if len(full_name) <= 1:
                        continue
                    name = full_name[1].strip()
                    ultimo_nome = full_name[0]
                    orientadores_old_names.append(name)
                    orientadores_old_ultimos_nomes.append(ultimo_nome)
                # Cria um recordset vazio
                orientadores = self.env['ud.biblioteca.publicacao.orientador'].search([('name', '=', False)])
                # busca por name e por ultimo_nome
                for i in xrange(len(orientadores_old_names)):
                    orientadores |= self.env['ud.biblioteca.publicacao.orientador'].search(
                        [('name', '=', orientadores_old_names[i]),
                         ('ultimo_nome', '=', orientadores_old_ultimos_nomes[i])]
                    )
                # Caso nem todas os orientadores estejam no banco, pula
                if len(orientadores) < len(orientadores_old_names):
                    _logger.error(
                        u'Nem todas os orientadores desta publicação estão cadastradas. Publicação: {}'.format(
                            pub['name']
                        )
                    )
                    continue
                # Coorientadores
                coorientadores_old = server.execute_kw(db, uid, password, 'ud.biblioteca.orientador', 'read',
                                                       [pub['coorientador_ids']])
                # Cria uma lista de "primeiros_nomes" e outra de "ultimos_nomes"
                coorientadores_old_names = []
                coorientadores_old_ultimos_nomes = []
                for o in coorientadores_old:
                    full_name = o['name'].split(',')
                    name = full_name[1].strip()
                    ultimo_nome = full_name[0]
                    coorientadores_old_names.append(name)
                    coorientadores_old_ultimos_nomes.append(ultimo_nome)
                # Cria um recordset vazio
                coorientadores = self.env['ud.biblioteca.publicacao.orientador'].search([('name', '=', False)])
                # busca por name e por ultimo_nome
                for i in xrange(len(coorientadores_old_names)):
                    coorientadores |= self.env['ud.biblioteca.publicacao.orientador'].search(
                        [('name', '=', coorientadores_old_names[i]),
                         ('ultimo_nome', '=', coorientadores_old_ultimos_nomes[i])]
                    )
                # Caso nem todas os orientadores estejam no banco, pula
                if len(coorientadores) < len(coorientadores_old_names):
                    _logger.error(
                        u'Nem todas os coorientadores desta publicação estão cadastradas. Publicação: {}'.format(
                            pub['name']
                        )
                    )
                    continue
                # Campus, polo e curso
                campus = self.env['ud.campus'].search([('name', '=', pub['ud_campus_id'][1])])
                polo = self.env['ud.polo'].search([('name', '=', pub['polo_id'][1])])
                curso = self.env['ud.curso'].search([('name', '=', pub['curso'][1])])
                # tipo de publicação
                tipo = self.env['ud.biblioteca.publicacao.tipo'].search([('name', '=', pub['tipo_id'][1])])
                # Caso não corresponda, pula
                if not tipo:
                    _logger.error(
                        u'Este tipo de publicação não está cadastradas. Publicação: {}'.format(
                            pub['name']
                        )
                    )
                    continue
                # autor
                full_name = pub['autor_id'][1].split(',')
                name = full_name
                ultimo_nome = ''
                if len(full_name) > 1:
                    name = full_name[1].strip()
                    ultimo_nome = full_name[0]
                autor = self.env['ud.biblioteca.publicacao.autor'].search(
                    [('name', '=', name), ('ultimo_nome', '=', ultimo_nome)])
                # Caso nem todas os orientadores estejam no banco, pula
                if not autor:
                    _logger.error(
                        u'O autor desta publicação não está cadastradas. Publicação: {}'.format(
                            pub['name']
                        )
                    )
                    continue
                pub_data = {
                    'name': pub['name'],
                    'campus_id': campus.id,
                    'polo_id': polo.id,
                    'curso_id': curso.id,
                    'tipo_id': tipo.id,
                    'ano_pub': pub['ano_pub'],
                    'autorizar_publicacao': pub['autorizar_publicacao'],
                }
                obj = self.create(pub_data)
                cont += 1
                if obj:
                    obj.orientador_ids |= orientadores
                    obj.coorientador_ids |= coorientadores
                    obj.palavras_chave_ids |= p_chave
                    obj.autor_ids |= autor
        _logger.warning(cont)
