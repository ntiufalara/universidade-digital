# -*- encoding: UTF-8 -*-
import copy

from openerp.osv import osv, fields
from openerp.osv.orm import except_orm


class ud_biblioteca_publicacao(osv.osv):
    """
    Nome: ud.biblioteca.publicacao
    Descrição: Cadastro de publicações do repositório institucional
    """
    _name = "ud.biblioteca.publicacao"

    """
    Atributo usado para salvar o Polo em caso de seleção manual (O navegador não envia valores de campos 'disabled')
    """
    __polo_id = 0

    _columns = {
        u'name': fields.char(u'Título', required=True), 'autor': fields.char(u'Autor'),
        u'autor_id': fields.many2one('ud.biblioteca.publicacao.autor', u'Autor', required=True),
        u'contato': fields.related('autor_id', 'contato', type="char", string=u"E-mail para contato"),
        u'ano_pub': fields.char(u'Ano de publicação', required=True),
        u'ud_campus_id': fields.many2one("ud.campus", u"Campus", required=True, change_default=True),
        u'curso': fields.many2one('ud.curso', u'Curso', ondelete='set null'),
        u"curso_indefinido": fields.boolean(u"Outro curso"),
        u"curso_indefinido_detalhes": fields.char(u"Curso"),
        u'observacoes': fields.text(u'Observações'),
        u'palavras_chave_ids': fields.many2many('ud.biblioteca.pc', 'ud_biblioteca_publicacao_pc_rel', 'pub_id',
                                                'pc_id', u'Palavras-chave', required=True),
        u'polo_id': fields.many2one('ud.polo', u'Polo', required=True, change_default=True),
        u'orientador_ids': fields.many2many('ud.biblioteca.orientador',
                                            'ud_biblioteca_publicacao_orientador_rel', 'pub_id',
                                            'orientador_id',
                                            string=u'Orientadores', required=True),
        u'coorientador_ids': fields.many2many('ud.biblioteca.orientador',
                                              'ud_biblioteca_publicacao_coorientador_rel', 'pub_id',
                                              'coorientador_id', string=u'Coorientadores'),
        u'anexo_ids': fields.one2many('ud.biblioteca.anexo', 'publicacao_id', u'Anexos em PDF', required=True),
        u'tipo': fields.selection((
            ('tcc', u'TCC'), ('dissertacao', u'Dissertação '), ('monografia', u'Monografia'),
            ('artigo', u'Artigo'), ('tese', u'Tese'), ('institucional', u'Material Institucional'),
            ('fotografia', u"Fotografia"), ('outros', u"Outros")), string=u'Tipo'),
        u'categoria_cnpq_id': fields.many2one('ud.biblioteca.publicacao.categoria_cnpq', u'Categoria CNPQ'),
        u'tipo_id': fields.many2one('ud.biblioteca.publicacao.tipo', u"Tipo", required=True),
        u"autorizar_publicacao": fields.boolean(u"Autorizar publicação"),
        u'visualizacoes': fields.integer(u'Visualizações', required=True),
        u'area_ids': fields.many2many('ud.biblioteca.publicacao.area', 'publicacao_ids',
                                      string=u'Áreas do trabalho', ),
    }

    _order = "ano_pub desc"

    _defaults = {'ud_campus_id': lambda self, cr, uid, context: self.busca_campus(cr, uid, context),
                 'polo_id': lambda self, cr, uid, context: self.busca_polo(cr, uid, context), 'visualizacoes': 0, }

    def read(self, cr, uid, ids, *args, **kwargs):
        """
        Contador de Visualizações
        :param cr:
        :param uid:
        :param ids:
        :return:
        """
        result = super(ud_biblioteca_publicacao, self).read(cr, uid, ids, *args, **kwargs)
        if type(ids) is not int and len(ids) == 1:
            for obj in result:
                if obj.get('visualizacoes') is not None:
                    vals = {'visualizacoes': obj.get('visualizacoes') + 1}
                    self.write(cr, 1, ids, vals)
                    obj['visualizacoes'] = vals['visualizacoes']
        return result

    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False):
        """
        Adiciona ordenação de cursos por nome na lista de publicações agrupada por curso
        :param cr:
        :param uid:
        :param domain:
        :param fields:
        :param groupby:
        :param offset:
        :param limit:
        :param context:
        :param orderby:
        :return:
        """
        if 'curso' in groupby:
            orderby = 'curso ASC' + (orderby and (',' + orderby) or '')
        return super(ud_biblioteca_publicacao, self).read_group(cr, uid, domain, fields, groupby, offset, limit,
                                                                context, orderby)

    def create(self, cr, user, vals, context=None):
        """
        Recupera o polo antes de  salvar
        Salva o contato do Autor no objeto "Autor"
        :param cr:
        :param user:
        :param vals:
        :param context:
        :return:
        """
        # Recuperando o Polo
        if self.__polo_id != 0 and not vals.get('polo_id'):
            vals['polo_id'] = self.__polo_id

        # Salvando contato do autor
        self.pool.get('ud.biblioteca.publicacao.autor').write(cr, user, [vals.get('autor_id')],
                                                              {'contato': vals.get('contato')})
        return super(osv.Model, self).create(cr, user, vals, context)

    def onchange_seleciona_polo(self, cr, uid, ids, polo_id):
        """
        Salva o valor do onchange para adicionar ao dicionário de criação.
        Fields disabled não são enviados ao servidor
        :param cr:
        :param uid:
        :param ids:
        :param polo_id:
        :return:
        """
        self.__polo_id = polo_id
        return {"value": {'polo_id': polo_id}}

    def busca_campus(self, cr, uid, context):
        """
        Localiza o Campus do qual ele é responsável, preenche o campo "campus_id"
        :param cr:
        :param uid:
        :param context:
        :return:
        """
        user_id = copy.copy(uid)
        uid = 1
        try:
            employee = self.pool.get('ud.employee').browse(cr, uid, self.pool.get('ud.employee').search(cr, uid, [
                ('resource_id.user_id', '=', user_id)]))[0]
        except:
            raise except_orm(u"O usuário precisa estar vinculado a pessoa para executar esta ação.",
                             u'Contate o administrador do sistema')
        responsavel_model = self.pool.get('ud.biblioteca.responsavel')
        responsavel_id = responsavel_model.search(cr, uid, [('employee_id', '=', employee.id)])
        responsavel_objs = responsavel_model.browse(cr, uid, responsavel_id)
        for obj in responsavel_objs:
            return obj.campus_id.id

    def busca_polo(self, cr, uid, context):
        """
        Busca o polo que o usuário é reponsável, caso ele seja administrador do campus, ele pode escolher.
        :param cr:
        :param uid:
        :param context:
        :return:
        """
        user_id = copy.copy(uid)
        uid = 1
        try:
            employee = self.pool.get('ud.employee').browse(cr, uid, self.pool.get('ud.employee').search(cr, uid, [
                ('resource_id.user_id', '=', user_id)]))[0]
        except:
            raise except_orm(u"O usuário precisa estar vinculado a pessoa para executar esta ação.",
                             u' Contate o administrador do sistema')
        responsavel_model = self.pool.get('ud.biblioteca.responsavel')
        responsavel_id = responsavel_model.search(cr, uid, [('employee_id', '=', employee.id)])
        responsavel_objs = responsavel_model.browse(cr, uid, responsavel_id)
        for obj in responsavel_objs:
            if obj.admin_campus:
                return None
            return obj.polo_id.id


class ud_biblioteca_publicacao_area(osv.Model):
    """
    Nome: ud.biblioteca.publicacao.area
    Descrição: Cadastro de área de trabalho
    """
    _name = 'ud.biblioteca.publicacao.area'

    _columns = {'name': fields.char(u'Área', required=True),
                'publicacao_ids': fields.many2many('ud.biblioteca.publicacao', 'area_ids', string=u'Publicações')}


class ud_bilbioteca_publicacao_categoria_cnpq(osv.Model):
    """
    Nome: ud.biblioteca.publicacao.categoria_cnpq
    Descrição: Cadastro de Categorias CNPQ
    """
    _name = 'ud.biblioteca.publicacao.categoria_cnpq'

    _columns = {'name': fields.char('Nome', required=True),
                'publicacao_ids': fields.one2many('ud.biblioteca.publicacao', 'categoria_cnpq_id')}


class ud_biblioteca_publicacao_tipo(osv.osv):
    '''
    Nome: ud.biblioteca.publicacao.tipo
    Descrição: Cadastro de tipos de publicações
    '''
    _name = 'ud.biblioteca.publicacao.tipo'

    _columns = {'name': fields.char('Tipo', required=True),
                'publicacao_ids': fields.one2many('ud.biblioteca.publicacao', 'tipo_id')}


class ud_publicacao_autor(osv.osv):
    """
    Nome: ud.biblioteca.publicacao.autor
    Descrição: Cadastro de autor de publicações
    """
    _name = "ud.biblioteca.publicacao.autor"

    _columns = {'name': fields.char('Nome', required=True), 'contato': fields.char('E-mail', required=False), }


class ud_biblioteca_orientador(osv.osv):
    """
    Nome: ud.biblioteca.orientador
    Deescrição: Relação many2many de publicação para orientador, permite adicionar mais de um orientador
    """
    _name = 'ud.biblioteca.orientador'
    _columns = {'name': fields.char('Nome', size=64, required=True),
                'titulacao_id': fields.many2one('ud.biblioteca.orientador.titulacao', "Titulação", required=True),
                'publicacao_orientador_id': fields.many2many('ud.biblioteca.publicacao',
                                                             'ud_biblioteca_publicacao_orientador_rel', 'orientador_id',
                                                             'pub_id', string=u'Orientador em'),
                'publicacao_coorientador_id': fields.many2many('ud.biblioteca.publicacao', 'coorientador_ids',
                                                               string=u'Coorientador em'), }

    def name_get(self, cr, uid, ids, context=None):
        objs = self.browse(cr, uid, ids, context)
        return [(obj.id, "{} {}".format(obj.titulacao_id.name, obj.name) if obj.titulacao_id else "{}".format(obj.name))
                for obj in objs]
        # return "{} {}".format(titulacao, name)


class ud_biblioteca_orientador_titulacao(osv.Model):
    """
    Nome: ud.biblioteca.orientador.titulacao
    Descrição: Relação Many2many de orientador para titulação, permite adicionar mais de uma titulação
    """
    _name = 'ud.biblioteca.orientador.titulacao'

    _columns = {'name': fields.char("Titulação", required=True),
                'orientador_ids': fields.one2many('ud.biblioteca.orientador', 'titulacao_id')}


class ud_biblioteca_anexo(osv.osv):
    """
    Nome: ud.biblioteca.anexo
    Deescrição: Arquivos contendo as publicações
    """
    _name = 'ud.biblioteca.anexo'
    _columns = {"name": fields.char("Anexo", required=True), 'arquivo': fields.binary('Arquivo PDF', filters="*.pdf"),
                'publicacao_id': fields.many2one('ud.biblioteca.publicacao', u'Publicação', required=False), }
    _defaults = {'publicacao_id': lambda self, cr, uid, context: self.publicacao_ctx(cr, uid, context), }

    def publicacao_ctx(self, cr, uid, context):
        """
        Retorna a publicação Atual usando o id de contexto
        """
        return context["active_id"]

    def unlink(self, cr, uid, ids, context=None):
        """
            Delete all record(s) from table heaving record id in ids
            return True on success, False otherwise

            @param cr: cursor to database
            @param uid: id of current user
            @param ids: list of record ids to be removed from table
            @param context: context arguments, like lang, time zone

            @return: True on success, False otherwise
        """

        return super(ud_biblioteca_anexo, self).unlink(cr, uid, ids, context=context)


class ud_biblioteca_pc(osv.osv):
    """
    Nome: ud.biblioteca.pc
    Descrição: Armazenar as palavras-chave de cada publicação
    """
    _name = 'ud.biblioteca.pc'

    _columns = {'name': fields.char('Palavra-chave', required=True),
                'publicacao_id': fields.many2many('ud.biblioteca.publicacao', 'ud_biblioteca_publicacao_pc_rel',
                                                  'pc_id', 'pub_id', 'Palavras-chave', ondelete='set null'), }


class ud_biblioteca_bibliotecario(osv.osv):
    _name = 'ud.biblioteca.responsavel'

    _get_name = lambda self, cr, uid, ids, field, args, context: self.get_name(cr, uid, ids, field, args, context)

    _columns = {'name': fields.function(_get_name),
                'employee_id': fields.many2one('ud.employee', u'Pessoa', required=True),
                'campus_id': fields.many2one('ud.campus', u'Campus', required=True),
                'admin_campus': fields.boolean(u'Administrador do campus'),
                'polo_id': fields.many2one('ud.polo', u'Polo', required=False)}

    def get_name(self, cr, uid, ids, field, args, context):
        res = {}
        for obj in self.browse(cr, uid, ids):
            polo_name = "--" if not obj.polo_id.name else obj.polo_id.name
            string = u"%s; Campus: %s; Polo: %s" % (obj.employee_id.name, obj.campus_id.name, polo_name)
            res[obj.id] = string
        return res
