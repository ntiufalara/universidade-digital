# -*- encoding: UTF-8 -*-
import copy

from openerp.osv import osv, fields
import re
from openerp.osv.orm import except_orm

class ud_biblioteca_publicacao(osv.osv):
    '''
    Nome: ud.biblioteca.publicacao
    Descrição: Cadastro de publicações do repositório institucional
    '''
    _name = "ud.biblioteca.publicacao"


    _columns = {
                'name' : fields.char(u'Título', required=True),
                'autor' : fields.char(u'Autor', required=True),
                'ano_pub' : fields.char(u'Ano de publicação',required=True),
                'ud_campus_id' : fields.many2one("ud.campus",u"Campus", required=True, change_default=True),
                'curso' : fields.many2one('ud.curso',u'Curso', ondelete='set null'),
                "curso_indefinido" : fields.boolean("Outro curso"),
                "curso_indefinido_detalhes" : fields.char("Curso"),
                'palavras-chave_ids':fields.many2many('ud.biblioteca.pc', 'ud_biblioteca_publicacao_pc_rel', 'pub_id', 'pc_id', u'Palavras-chave', required=True),
                'polo_id' : fields.many2one('ud.polo', u'Polo', required=True, change_default=True),
                'orientador_ids':fields.many2many('ud.biblioteca.orientador', 'ud_biblioteca_publicacao_orientador_rel', 'pub_id', 'orientador_id', string='Orientadores', required=True),
                'coorientador_ids':fields.many2many('ud.biblioteca.orientador', 'ud_biblioteca_publicacao_coorientador_rel', 'pub_id', 'coorientador_id', string='Coorientadores'),
                'anexo_ids':fields.one2many('ud.biblioteca.anexo', 'publicacao_id', u'Anexos em PDF', required=True),
                'tipo':fields.selection((
                    ('tcc','TCC'),
                    ('dissertacao',u'Dissertação '),
                    ('monografia',u'Monografia'),
                    ('artigo',u'Artigo'),
                    ('tese',u'Tese'),
                    ('institucional',u'Material Institucional'),
                    ('fotografia',"Fotografia"),
                    ('outros',u"Outros")
                     ),    string=u'Tipo'),
                "autorizar_publicacao" : fields.boolean(u"Autorizar publicação"),
                }

    _order = "ano_pub desc"

    _defaults = {
        'ud_campus_id': lambda self,cr,uid,context: self.busca_campus(cr,uid,context),
        'polo_id': lambda self, cr, uid, context: self.busca_polo(cr,uid,context)
        }

    def busca_campus (self, cr,uid,context):
        user_id = copy.copy(uid)
        uid = 1
        try:
            employee = self.pool.get('ud.employee').browse(cr, uid,
                                                           self.pool.get('ud.employee').search(cr, uid, [
                                                               ('resource_id.user_id', '=', user_id)]))[0]
        except:
            raise except_orm("O usuário precisa estar vinculado a pessoa para executar esta ação.")
        responsavel_model = self.pool.get('ud.biblioteca.responsavel')
        responsavel_id = responsavel_model.search(cr, uid, [('employee_id', '=', employee.id)])
        responsavel_objs = responsavel_model.browse(cr, uid, responsavel_id)
        for obj in responsavel_objs:
            return obj.campus_id.id

    def busca_polo(self, cr, uid, context):
        user_id = copy.copy(uid)
        uid = 1
        try:
            employee = self.pool.get('ud.employee').browse(cr, uid,
                                                           self.pool.get('ud.employee').search(cr, uid, [
                                                               ('resource_id.user_id', '=', user_id)]))[0]
        except:
            raise except_orm("O usuário precisa estar vinculado a pessoa para executar esta ação.")
        responsavel_model = self.pool.get('ud.biblioteca.responsavel')
        responsavel_id = responsavel_model.search(cr, uid, [('employee_id', '=', employee.id)])
        responsavel_objs = responsavel_model.browse(cr, uid, responsavel_id)
        for obj in responsavel_objs:
            if obj.admin_campus:
                return False
            return obj.polo_id.id


class ud_biblioteca_orientador (osv.osv):
    '''
    Nome: ud.biblioteca.orientador
    Deescrição: Relação many2many de publicação para orientador, permite adicionar mais de um orientador
    '''
    _name = 'ud.biblioteca.orientador'
    _columns = {
            'name':fields.char('Nome', size=64, required=True),
            'publicacao_orientador_id':fields.many2many('ud.biblioteca.publicacao','orientador_ids', string=u'Publicação'),
            'publicacao_coorientador_id':fields.many2many('ud.biblioteca.publicacao','coorientador_ids', string=u'Publicação'),
    }

class ud_biblioteca_anexo(osv.osv):
    '''
    Nome: ud.biblioteca.anexo
    Deescrição: Arquivos contendo as publicações
    '''
    _name = 'ud.biblioteca.anexo'
    _columns = {
            "name" : fields.char("Anexo", required=True),
            'arquivo':fields.binary('Arquivo PDF', filters="*.pdf"),
            'publicacao_id':fields.many2one('ud.biblioteca.publicacao', u'Publicação', required=False),
    }
    _defaults = {
        'publicacao_id': lambda self, cr, uid, context: self.publicacao_ctx(cr, uid, context),
    }

    def publicacao_ctx(self, cr, uid, context):
        '''
        Retorna a publicação Atual usando o id de contexto
        '''
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
    '''
    Nome: ud.biblioteca.pc
    Descrição: Armazenar as palavras-chave de cada publicação
    '''
    _name = 'ud.biblioteca.pc'

    _columns = {
            'name':fields.char('Palavra-chave', required=True),
            'publicacao_id':fields.many2one('ud.biblioteca.publicacao', 'publicacao'),
    }


class ud_biblioteca_bibliotecario(osv.osv):
    _name = 'ud.biblioteca.responsavel'

    _get_name = lambda self, cr, uid, ids, field, args, context: self.get_name(cr, uid, ids, field, args, context)

    _columns = {
        'name': fields.function(_get_name),
        'employee_id': fields.many2one('ud.employee', u'Pessoa', required=True),
        'campus_id': fields.many2one('ud.campus', u'Campus', required=True),
        'admin_campus': fields.boolean(u'Administrador do campus'),
        'polo_id': fields.many2one('ud.polo', u'Polo', required=False)
    }

    def get_name(self, cr, uid, ids,  field, args, context):
        res = {}
        for obj in self.browse(cr, uid, ids):
            polo_name = "--" if not obj.polo_id.name else obj.polo_id.name
            string = u"%s; Campus: %s; Polo: %s" % (obj.employee_id.name, obj.campus_id.name, polo_name)
            res[obj.id] = string
        return res
