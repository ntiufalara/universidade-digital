# -*- encoding: UTF-8 -*-

from openerp.osv import osv, fields
import re
from openerp.osv.orm import except_orm

class ud_biblioteca_publicacao(osv.osv):
    '''
    Nome: ud.biblioteca.publicacao
    Descrição: Cadastro de publicações do repositório institucional
    '''
    _name = "ud.biblioteca.publicacao"
    
    def _user_admin(self, cr, uid, *arg, **kwarg):
        res = True
        cr.execute("""SELECT 
                            res_groups.name
                        FROM
                            res_groups_users_rel,
                            res_groups
                        WHERE 
                            res_groups.name like 'Bibliotecário%'
                            and
                            res_groups.id=res_groups_users_rel.gid
                            and
                            res_groups_users_rel.uid = {};""".format(uid))
        result = cr.fetchall()
        if result:
            if any(map(lambda l: "Admin" in l[0], result)):
                res = False
        return res
    
    def _somente_leitura(self, cr, uid, ids, context = {}, *arg, **kwarg):
        if isinstance(ids, (int, long)):
            ids = [ids]
        return {}.fromkeys(ids, self._user_admin(cr, uid))
        
    _columns = {
                'name' : fields.char(u'Título', required=True),
                'autor' : fields.char(u'Autor', required=True),
                'ano_pub' : fields.char(u'Ano de publicação',required=True),
                'ud_campus_id' : fields.many2one("ud.campus",u"Campus", required=True, readonly=True, change_default=True),
                'curso' : fields.many2one('ud.curso',u'Curso', ondelete='set null'),
                "curso_indefinido" : fields.boolean("Outro curso"),
                "curso_indefinido_detalhes" : fields.char("Curso"),
                'palavras-chave_ids':fields.many2many('ud.biblioteca.pc', 'ud_biblioteca_publicacao_pc_rel', 'pub_id', 'pc_id', u'Palavras-chave', required=True),
                "polo_somente_leitura": fields.function(_somente_leitura, type = "boolean", store = False, method = True,
                                                   string = u"Polo Somente Leitura", invisible = True),
                'polo_id' : fields.many2one('ud.polo', u'Polo', required=True, readonly=True, change_default=True),
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
        'polo_id': lambda self,cr,uid,context: self.polo_default(cr,uid,context),
        'ud_campus_id': lambda self,cr,uid,context: self.busca_campus(cr,uid,context),
        'polo_somente_leitura': lambda self, cr, uid, context: self._user_admin(cr, uid),
        }
    
    def busca_campus (self, cr,uid,context):
        exp_campus = re.compile(r'[a-zA-Z]*[arapiraca]')
        cr.execute('''
            SELECT ud_campus.id
            FROM ud_campus
        ''')
        try:
            lista_campus = list(cr.fetchall()[0])
        except:
            raise except_orm(u"Não é possível localizar o Campus Arapiraca", u"É preciso que o campus Arapiraca esteja cadastrado corretamente")
        campus = self.pool.get('ud.campus').browse(cr,uid,lista_campus)
        for camp in campus:
            if exp_campus.match(camp.name.lower()):
                return camp.id
          
    def polo_default(self, cr, uid, context):
        cr.execute("""SELECT
                          ud_employee.polo_id
                      FROM
                          ud_employee,
                          res_users
                      WHERE
                          res_users.id=%d
                          and
                          ud_employee.user_id=res_users.id""" %uid)
        result = cr.fetchall()
        if result:
            return result[0]
        return None
    
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