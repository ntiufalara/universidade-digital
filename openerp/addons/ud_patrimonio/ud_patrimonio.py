# -*- encoding: utf-8 -*-

from openerp.osv import osv, fields


class patrimonio_marca(osv.osv):
    '''
    Classe que representa a entida do formulário Marca.
    '''
    _name = 'patrimonio.marca'
    _description = "Marca"
    
    _columns = {
        u'name': fields.char(u'Nome', size=120, required=True),
        u'descricao':fields.text(u'Descrição')
                
    }
 
patrimonio_marca()

class patrimonio_modelo_propriedade(osv.osv):
    
    '''
    Classe que representa a entidade do formulário Propriedades.
    '''
    
    _name = 'patrimonio.modelo.propriedade'
    _description = "Propriedades do Modelo"
    
    _columns = {
        u'name':fields.char(u'Descrição', size=120, required=True),
        u'valor':fields.char(u'Valor', size=120, required=True),
        u'modelo_propriedade_id':fields.many2one('patrimonio.modelo', 'Propriedade', ondelete='cascade', invisible=True),
                
    }
    
patrimonio_modelo_propriedade()

class patrimonio_modelo(osv.osv):
    '''
    Classe que representa a entidade do formulário Modelo.
    '''
    _name = 'patrimonio.modelo'
    _description = "Modelo"
    
    _columns = {
        u'name': fields.char(u'Nome', size=120, required=True),
        u'marca': fields.many2one(u'patrimonio.marca', u"Marca", ondelete="cascade", required=True, help="Ex.: Philips"),
        u'descricao':fields.text(u'Descrição'),
        u'propriedade_ids':fields.one2many('patrimonio.modelo.propriedade', 'modelo_propriedade_id', 'Propriedade', ondelete='cascade')
                
    }
patrimonio_modelo()

class patrimonio_grupo(osv.osv):
    '''
    Classe que representa a entidade do formulário Grupo do bem.
    '''
    _name = 'patrimonio.grupo'
    _description = "Grupo"
    
    _columns = {
        u'name': fields.char(u'Nome', size=120, required=True),
        u'descricao':fields.text(u'Descrição')
                
    }
patrimonio_grupo()

class patrimonio_estado(osv.osv):
    '''
    Classe que representa a entidade do formulário Estado do bem.
    '''
    _name = 'patrimonio.estado'
    _description = "Estado"
    
    _columns = {
        u'name': fields.char(u'Nome', size=120, required=True),
        u'descricao':fields.text(u'Descrição')
                
    }
patrimonio_estado()

class patrimonio_bem(osv.osv):
    '''
    Classe que representa a entidade do formulário Bem.
    '''
    _name = 'patrimonio.bem'
    _description = "Bem"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    
    _columns = {
        u'name': fields.char(u'Nº Patrimônio/Nº Série', size=120, required=True),
        u'nome': fields.char(u'Nome', size=120, required=True),        
        u'espaco': fields.many2one('ud.espaco', u"Espaco Lotado", ondelete="cascade", required=True),
        u'grupo': fields.many2one('patrimonio.grupo', u"Grupo", ondelete="cascade", required=True),
        u'estado': fields.many2one('patrimonio.estado', u"Estado", ondelete="cascade", required=True),
        u'modelo': fields.many2one('patrimonio.modelo', u"Modelo", ondelete="cascade", required=True), 
        u'marca_local': fields.many2one('patrimonio.marca', u'Marca', required=True),
        u'descricao':fields.text(u'Descrição'),
        u'marca_filtro': fields.related('modelo', 'marca.name', type='char'),
        u'solicitacao_os' : fields.one2many('ud.solicitacao', 'pat', "solicitacao"),
    }

    def create(self, cr, uid, values, context=None):
        context['mail_create_nolog'] = True
        return super(patrimonio_bem, self).create(cr, uid, values, context)
    
    def limpa_modelo(self, cr, uid, ids):
        '''
        Limpa o campo modelo se o mesmo não pertence ao bem.
        '''
        campos = ["modelo"]
        valores = {}
        for campo in campos:
            valores[campo] = ""
        print valores
        return {'value':valores}


    _sql_constraints = [('patrimonio_numero_uniq', 'unique(name)',u'Já existe Patrimônio referente a este número!')]
patrimonio_bem()
    

    
