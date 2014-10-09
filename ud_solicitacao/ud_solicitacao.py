#coding:utf8

from openerp.osv import fields, osv
from openerp.osv.orm import except_orm

class ud_nova_solicitacao (osv.osv):
    '''
    Objeto principal do módulo de ordem de serviço. Contém todos os campos do usados na solicitação de OS
    '''
    
    _name = 'ud.solicitacao'
    
    _matricula = lambda self, cr, uid, ids, field, args, context: self.busca_dados(cr, uid, ids, field,args, context)
    _telefone = lambda self, cr, uid, ids, field, args, context: self.busca_dados(cr, uid, ids, field,args, context)
    _email = lambda self, cr, uid, ids, field, args, context: self.busca_dados(cr, uid, ids, field,args, context)
    _setor = lambda self, cr, uid, ids, field, args, context: self.busca_dados(cr, uid, ids, field,args, context)

    _inherit = ['mail.thread', 'ir.needaction_mixin']
    
    # Estrutura com todos os estados possíveis de solicitação
    status = (("nova","Solicitação enviada"),("atribuida",'Análise'),("aprovada","Encaminhado p/ Execução"),("execucao","Em Execução"),("finalizada", "Finalizada"),("cancelada","Cancelada"),)
    
    _columns = {
                'solicitante_id':fields.many2one("ud.employee",'Solicitante', required=True, ondelete="cascade"),
                'matricula':fields.function(_matricula,string=u"Matrícula",type="char",required=True),
                'setor_id':fields.function(_setor,string='Setor / Curso',type="char", required=True),
                'email':fields.function(_email, string="E-mail",type="char", required=True),
                'telefone':fields.function(_telefone, string='Telefone',type="char", required=True),
                'data':fields.date('Data da Solicitação', required=True),
				'state':fields.selection(status,'Status'),
                'motivo':fields.text("Motivo ",),
                'responsavel':fields.many2one('ud.solicitacao.responsavel','Responsavel',),
                "previsao":fields.date("Previsão para a execução",),
                "execucao":fields.text("Descrição do serviço",),
                "data_execucao":fields.date("Data da execução", ),
                "finalizar":fields.text("Serviço Executado", ),
                "data_cancelamento": fields.date("Data de cancelamento"),
                
                "manutencao":fields.selection((("equip","Equipamento"),("pred","Predial"),("limp","Limpeza"),("movmat","Movimentação de Materiais")),"Manutenção", required=True),
                
                "mov_denominacao":fields.char("Denominação"),

                    "equipamento":fields.selection((("elt","Elétricos"),("hid","Hidráulicos")), "Equipamentos"),
                        "eq_eletricos":fields.selection( (('apref',"Refrigeradores"),("info", u"Informática"),("outros","Outros")), "Tipo de equipamento"),
                        "equip_denominacao":fields.char("Nome do equipamento"),
                        "modelo":fields.char("Modelo"),
                        "marca":fields.char("Marca"),
                        "modelo1":fields.char("Modelo"),
                        "marca1":fields.char("Marca"),
                            "refrigeradores":fields.selection( (("arc","Ar Condicionado"),("outrod","Outros (Geladeiras, Bebedouros etc)")),"Tipo de refrigerador" ),
                                "ref_tipo": fields.selection( (("split", "Split"),("janela","Janela")), "Tipo de ar condicionado"),                    
                    "predial":fields.selection( (('inst','Instalações'),('alv','Alvenaria / Esquadrias / Metálicas / Divisórias')), "Manutenção predial"),
                        "instalacoes":fields.selection( (('elt','Elétricas'),("hid", "Hidráulicas")), "Instalações"),
                
                        
                "local_camp": fields.many2one("ud.campus", "Campus", required=True),
                "local_polo": fields.many2one("ud.polo","Polo", required=True),
                "local_espaco": fields.many2one("ud.espaco","Espaço", required=True),
                "detalhes_espaco": fields.char('Sala / Bloco'),
                "local_camp_destino": fields.many2one("ud.campus", "Campus"),
                "local_polo_destino": fields.many2one("ud.polo","Polo"),
                "local_espaco_destino": fields.many2one("ud.espaco","Espaço"),
                "detalhes_espaco_destino": fields.char('Sala / Bloco'),
                "pat":fields.char("Patrimônio ref."),
                "pat_bool":fields.boolean("Patrimônio"),
                'descricao':fields.text('Descrição', required=True),
                    
                }
    _defaults = {
                'solicitante_id':lambda self,cr,uid,c: self.obter_nome(cr, uid, c),
#                 'matricula':lambda self, cr, uid, c: self.matricula(cr, uid, c),
#                 'setor_id':lambda self, cr, uid, c: self.setor(cr,uid,c),
#                 'telefone':lambda self, cr, uid, c: self.telefone(cr, uid, c),
#                 "email":lambda self,cr,uid,c: self.email(cr, uid, c),
                'data':lambda self,cr,uid,c: fields.date.today()
                 }
    _rec_name = "data"
    
    def busca_dados (self, cr, uid, ids, field, args, context):
        dados = self.browse(cr, uid, ids, context)[0]
        if field == "matricula":
            if self.browse(cr, uid, ids, context)[0].solicitante_id.papel_ids[0].matricula != None:
                return {dados.id:self.browse(cr, uid, ids, context)[0].solicitante_id.papel_ids[0].matricula}
            else:
                raise except_orm(u"Matrícula não encontrada", u"Pessoa não possui nenhuma matrícula")
        elif field == "telefone":
            if self.browse(cr, uid, ids, context)[0].solicitante_id.mobile_phone != None:
                return {dados.id:self.browse(cr, uid, ids, context)[0].solicitante_id.mobile_phone}
            elif self.browse(cr, uid, ids, context)[0].solicitante_id.work_phone != None:
                return {dados.id : self.browse(cr, uid, ids, context)[0].solicitante_id.work_phone }
            else:
                raise except_orm(u"Telefone não encontrado", u"É necessário ao menos um telefone cadastrado")
        elif field == "setor_id":
            if self.browse(cr, uid, ids, context)[0].solicitante_id.papel_ids[0].ud_setores.name != None:
                return {dados.id:self.browse(cr, uid, ids, context)[0].solicitante_id.papel_ids[0].ud_setores.name}
            elif self.browse(cr, uid, ids, context)[0].solicitante_id.papel_ids[0].ud_cursos.name != None:
                return {dados.id : self.browse(cr, uid, ids, context)[0].solicitante_id.papel_ids[0].ud_cursos.name}
            else:
                raise except_orm(u"Setor não encontrado", u"Pessoa está vinculada a nenhum setor")
        elif field == "email":
            if self.browse(cr, uid, ids, context)[0].solicitante_id.work_email != None:
                return {dados.id:self.browse(cr, uid, ids, context)[0].solicitante_id.work_email}
            else:
                raise except_orm(u"E-mail não encontrado", u"É necessário existir um e-mail cadastrado")
    
    def limpa_mnt (self, cr, uid, ids):
        '''
        Limpa os campos dependentes
        método on_change
        '''
        campos = ["mov_denominacao","equipamento","eq_eletricos","equip_denominacao","modelo","marca","refrigeradores","ref_tipo","predial","instalacoes","pat","pat_bool","local_camp_destino","local_polo_destino","local_bloco_destino","local_sala_destino"]
        valores = {}
        for campo in campos:
            valores[campo] = ""
        
        return {'value':valores}

    def limpa_equip (self, cr, uid, ids):
        '''
        Limpa os campos dependentes
        método on_change
        '''
        campos = ["eq_eletricos","equip_denominacao","modelo","marca","refrigeradores","ref_tipo"]
        valores = {}
        for campo in campos:
            valores[campo] = ""
        return {'value':valores}

    def limpa_tipo_equip (self, cr, uid, ids):
        '''
        Limpa os campos dependentes
        método on_change
        '''
        campos = ["equip_denominacao","modelo","marca","refrigeradores","ref_tipo"]
        valores = {}
        for campo in campos:
            valores[campo] = ""
        print valores
        return {'value':valores}
    
    def limpa_pred (self, cr, uid, ids):
        '''
        Limpa os campos dependentes
        método on_change
        '''
        campos = ["instalacoes","pat","pat_bool"]
        valores = {}
        for campo in campos:
            valores[campo] = ""
        
        return {'value':valores}
    
    def onchange_solicitante(self, cr, uid,ids, solicitante, context=None):
        pessoa = self.pool.get("ud.employee").search(cr, uid, [('id','=',solicitante)], 0)
        papel = self.pool.get('ud.perfil').search(cr,uid,[('ud_papel_id','=',solicitante)], 0)
        # Browse Record Obj
        pessoa = self.pool.get('ud.employee').browse(cr,uid,pessoa)[0]
        papel = self.pool.get('ud.perfil').browse(cr,uid,papel)[0]
        
        setor_curso = papel.ud_setores.name or papel.ud_cursos.name
        
        return {'value': {'matricula': papel.matricula, 'telefone':pessoa.mobile_phone, 'email':pessoa.work_email,'setor_id': setor_curso}}
    
    def obter_nome(self, cr, uid, c):
        '''
        Obtém o id da pessoa associada ao usuário logado e devolve para o campo relacional "solicitante_id"
        '''
        cr.execute('''SELECT 
                      ud_employee.id
                    FROM 
                      public.ud_employee, 
                      public.resource_resource, 
                      public.res_users
                    WHERE 
                      res_users.id = %s AND
                      ud_employee.resource_id = resource_resource.id AND
                      resource_resource.user_id = res_users.id;''' %(uid))
        pessoa = cr.fetchone()
        if pessoa:
            if pessoa[0] != None:
                return pessoa[0]
        else:
            raise except_orm("Pessoa não localizada".decode("UTF-8"), "Não há pessoa associada a esse usuário".decode("UTF-8"))

    def matricula (self, cr, uid, c):
        '''
        Retorna a matrícula do usuário logado, do seu primeiro papel.
        '''
        cr.execute('''SELECT ud_perfil.matricula
                        FROM 
                          public.res_users, 
                          public.resource_resource, 
                          public.ud_employee, 
                          public.ud_perfil
                        WHERE 
                          res_users.id = %d AND
                          resource_resource.user_id = res_users.id AND
                          ud_employee.resource_id = resource_resource.id AND
                          ud_perfil.ud_papel_id = ud_employee.id;''' % (uid))
        matricula = cr.fetchone()
        if matricula:
            if matricula[0] != None:
                return matricula[0]
        else:
            raise except_orm("Pessoa não localizada".decode("UTF-8"), "É necessário que a pessoa tenha um papel para realizar solicitações".decode("UTF-8"))

    def telefone (self, cr, uid, c):
        '''
        Retorna o telefone cadastrado
        '''
        cr.execute('''SELECT 
                          ud_employee.mobile_phone
                        FROM 
                          public.ud_employee, 
                          public.resource_resource, 
                          public.res_users
                        WHERE 
                          res_users.id = %d AND
                          ud_employee.resource_id = resource_resource.id AND
                          resource_resource.user_id = res_users.id;''' % (uid))
        telefone = cr.fetchone()
        if telefone:
            if telefone[0] != None:
                return telefone[0]
        else:
            raise except_orm("Pessoa não possui telefone".decode("UTF-8"), "É necessário possuir um telefone cadastrado para realizar solicitações".decode("UTF-8"))

    def setor (self,cr,uid,c):
        '''
        Retorna o setor ou o curso do primeiro papel cadastrado
        '''
        cr.execute('''SELECT   ud_setor.name 
                        FROM   public.ud_perfil,   
                                public.ud_setor,     
                                public.ud_employee, 
                                public.resource_resource,
                                 public.res_users
                        WHERE   res_users.id = %d AND
                                ud_perfil.ud_setores = ud_setor.id AND
                                ud_perfil.ud_papel_id = ud_employee.id AND
                                ud_employee.resource_id = resource_resource.id AND
                                resource_resource.user_id = res_users.id;'''% (uid))
        
        setor = cr.fetchall()
        
        cr.execute('''SELECT
                        ud_curso.name 
                FROM   public.ud_perfil,   
                        public.ud_curso,   
                        public.ud_employee, 
                        public.resource_resource,
                         public.res_users
                WHERE   res_users.id = %d AND
                        ud_perfil.ud_cursos = ud_curso.id AND
                        ud_perfil.ud_papel_id = ud_employee.id AND
                        ud_employee.resource_id = resource_resource.id AND
                        resource_resource.user_id = res_users.id;'''% (uid))
        curso = cr.fetchall()
        setores_cursos = setor + curso
        if setores_cursos:
            if setores_cursos[0] != None:
                return setores_cursos[0][0]
        raise except_orm("Pessoa não possui papel".decode("UTF-8"), "É necessário que a pessoa tenha um papel para realizar solicitações".decode("UTF-8"))
    
    def email (self, cr, uid, c):
        '''
        Retorna o email do usuário atual
        '''
        
        cr.execute('''SELECT 
                          ud_employee.work_email
                        FROM 
                          public.ud_employee, 
                          public.resource_resource, 
                          public.res_users
                        WHERE 
                          res_users.id = %d AND
                          ud_employee.resource_id = resource_resource.id AND
                          resource_resource.user_id = res_users.id;''' % (uid))
        email = cr.fetchone()
        if email:
            if email[0] != None:
                return email[0]
        else:
            raise except_orm("Pessoa não possui e-mail".decode("UTF-8"), "É necessário que a pessoa tenha um email cadastrado para realizar solicitações".decode("UTF-8"))
 
    
    def onchange_espaco_destino (self, cr, uid, ids, espaco):
        '''
        Recupera e gera detalhes do espaço (Bloco / Sala)
        '''
        cr.execute('''
                    SELECT
                        ud_bloco.name
                    FROM
                        ud_espaco,
                        ud_bloco
                    WHERE
                        ud_espaco.id = %d AND
                        ud_espaco.local_bloco_polo = ud_bloco.id
                    ''' % (espaco))
        bloco = cr.fetchone()
        
        cr.execute('''
                    SELECT
                        ud_sala.name
                    FROM
                        ud_espaco,
                        ud_sala
                    WHERE
                        ud_espaco.id = %d AND
                        ud_espaco.local_sala_polo = ud_sala.id
                    ''' % (espaco))
        sala = cr.fetchone()
        
        string = " %s - %s" % ( bloco[0], sala[0] )
        return {"value":{"detalhes_espaco_destino":string}}
        
    # Troca o Status para "Cancelado"
    def cancelar (self, cr, uid, ids, context):
        '''
        Grava o motivo e o status cancelado na solicitação atual.
        Acionado por um botão
        '''
        slc = self.browse(cr,uid,ids,context)[0]
        if slc.motivo and slc.state != "finalizada":
            self.write(cr, uid, ids, {"motivo":slc.motivo,'state': 'cancelada'}, context=context)
    # Executar Solicitação de Serviço
    def execucao(self, cr, uid, ids, ctx):
        '''
        Grava o status em execução na solicitação atual
        Acionado por umn botão
        '''
        slc = self.browse(cr,uid,ids,ctx)[0]
        if slc.state == "aprovada" and slc.execucao:
            return self.write(cr, uid, ids, {"state":"execucao", "execucao":slc.execucao, "data_execucao":fields.datetime.now()},context=ctx)

    # Finalizar a Solicitação de serviço
    def finalizar (self,cr,uid,ids,ctx):
        '''
        Grava o status "Finalizado" na solicitação atual
        Acionado por umn botão
        '''
        slc = self.browse(cr,uid,ids,ctx)[0]
        if slc.state == "execucao" and slc.finalizar and slc.tempo_gasto:
            return self.write( cr,uid, ids, {"state":"finalizada", "finalizar":slc.finalizar, "tempo_gasto":slc.tempo_gasto}, context=ctx )
        
    def envia_solicitacao(self, cr, uid, ids,c=None):
        status = self.browse(cr,uid, ids)[0].state
        if not status:
            self.write(cr, uid, ids, {"state":"nova"})
            return True
        return True
     
    _constraints = [(envia_solicitacao, "Solicitação Enviada", ["Enviar"])]
    