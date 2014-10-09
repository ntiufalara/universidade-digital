# -*- encoding: UTF-8 -*-

from openerp.osv import osv, fields
from openerp.osv.orm import except_orm
from datetime import datetime
from Tkconstants import SOLID

class transporte_motorista(osv.osv):
    '''
    Nome: ud.transporte.motorista
    descrição: Representa o cadastro de motoristas vinculados a instituição
    '''
    
    _name = 'ud.transporte.motorista'
    
    _columns = {
                'name':fields.char('Nome', size=64, required=True),
                'cpf':fields.char('CPF', required=True),
                'cnh': fields.char('CNH', size=11, required=True, help="Ex.: xxxxxxxxxxxx"),
                'data_vencimento':fields.char('Data de vencimento',help="Informe a data de vencimento da CNH", required=True),
                'matricula': fields.char(u'Matrícula', size=10, help="11111111", required=True), 
                'categoria': fields.selection(
                                    (('a','A'),('b','B'),('c','C'),('d','D'),
                                    ('e','E'),('ab','AB'),('ac','AC'),('ad','AD'),('ae','AE')),
                                    string='Categoria',
                                    help="A, AB, B"
                                    ),
                'telefone': fields.char('Telefone', size=12, help="Ex.: XX-XXXX-XXXX", required=True),
                'state': fields.selection(
                                    (('ativo', 'Ativo'),('inativo', 'Inativo')),
                                    string='Estado'
                                    ),
                'endereco': fields.char(u'Endereço', size=120),
                'bairro': fields.char('Bairro', size=32),
                'cidade': fields.char( 'Cidade'),
                'estado': fields.selection([('ac', 'AC'), ('al', 'AL'), ('ap', 'AP'), ('am', 'AM'), ('ba','BA'), ('ce','CE'), ('df','DF'), ('es','ES'), ('go','GO'), ('ma','MA') , ('mg','MG'), ('ms','MS'), ('mt','MT'), ('pa','PA'), ('pe','PE'), ('pi','PI'), ('pr','PR'), ('rj','RJ'), ('rn','RN'), ('ro','RO'), ('rr','RR'), ('rs', 'RS'), ('sc','SC'), ('se','SE'), ('sp','SP'), ('to', 'TO')], 'Estado', required=True),
                'empresa':fields.many2one('ud.transporte.empresa', "Empresa", required=True,),
                'local':fields.many2one("ud.polo", "Lotado", required=True),
                'data_admissao':fields.char(u"Data de admissão", required=True),
                }
    
    _defaults = {  
        'state': lambda *a: 'ativo',  
        }
    
    def create (self, cr, uid, values, context=None):
        '''
        Função: Reescrita osv.create()
        Descrição: Verifica, antes de salvar, se os valores de CNH e Matrícula já estão cadastrados
        '''
        cnh = self.search(cr, uid, [('cnh','=',values['cnh'])], 0)
        matricula = self.search(cr, uid, [('matricula','=',values['matricula'])], 0)
        if cnh:
            raise except_orm(u'Erro ao salvar CNH', u'CNH duplicada')
        elif matricula:
            raise except_orm(u'Erro ao salvar Matricula', u'Matricula duplicada')
        else:
            return super(osv.osv, self).create(cr,uid,values,context)
        
    def status_ativo(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'ativo'})
    def status_inativo(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'inativo'})

class transporte_empresa (osv.osv):
    '''
    Nome: ud.transporte.empresa
    descrição: Representa o cadastro das empresas de transporte vinculados a instituição
    '''
    _name = 'ud.transporte.empresa'
    
    _columns = {
                'name':fields.char('Nome', size=64, required=True),
                'motorista_ids':fields.one2many('ud.transporte.motorista', 'empresa', 'motorista'),
                } 
    
class transporte_veiculo(osv.osv):
    '''
    Nome: ud.transporte.veiculo
    descrição: Representa o cadastro de veículos vinculados a instituição
    '''
    _name = 'ud.transporte.veiculo' 
    
    _columns = {
                'placa':fields.char('Placa',size=8),
                'renavam':fields.char('Renavam',size=12),
                'chassis':fields.char('Chassis',size=20),
                'notas':fields.text('Notas'),

                'ano':fields.char('Ano',size=4, required=True),
                'marca':fields.char('Marca',size=10, required=True),
                'modelo':fields.char('Modelo',size=15, required=True),
                'cor':fields.char('Cor',size=15),
                'tipo_de_veiculo': fields.selection([
                        ("moto","Moto"),
                        ('caminhao','Caminhão'),
                        ('onibus','Ônibus'),
                        ('carro','Carro'),
                        ('outro','Outro')], 'Tipo de veículo', required=False,),
                'state': fields.selection([
                        ('ativo','Ativo'),
                        ('foradeservico','Fora de Serviço'),
                        ('inutilizavel','Inutilizável'),
                        ], 'Status', required=True,),
                'propriedade': fields.selection([
                        ('propriedade','Propriedade'),
                        ('privado','Privado (propriedade do empregado)'),
                        ('arrendado','Arrendado'),
                        ('Alugado','Alugado'),                       
                        ], u'Proprietário', required=False), 
                        
                'medidor_primario':fields.selection([
                                                 ('odometro','Odômetro'),
                                                 ('metrohora','Metro por Hora'),
                                                 ],'Metragem inicial',required=False),
                'tipo_de_combustivel':fields.selection([
                                             ('95','95 (Euro)'),
                                             ('98','98 (Super)'),
                                             ('E85','E85 (Etanole)'),
                                             ('B','Biogas'),
                                             ('D','Diesel'),
                                             ('Electric','Electric'),
                                             ],u'Tipo de combustível',required=False),
                'tanque':fields.float('Capacidade do tanque'),
                'local':fields.many2one('ud.polo', "Local", required=True),
                'manutencao_ids':fields.one2many('ud.transporte.manutencao', 'veiculo', 'menutencao'),
                }
    
    _defaults={
               'tipo_de_veiculo':lambda *a:'carro',
               'state':lambda *a:'ativo',
               'propriedade':lambda *a:'propriedade',
               'tipo_de_combustivel':lambda *a:'D',
               }
    _rec_name = 'modelo' 
    def _verifica_placa (self, cr, uid, ids, ctx=None):
        '''
        Função: Verifica repetições
        '''
        placa = self.read(cr, uid, ids, ctx)[0]["placa"]
        cr.execute(''' SELECT placa FROM ud_transporte_veiculo WHERE placa = '%s'  ''' % (placa))
        result = cr.fetchall()
        if len(result) > 1:
            return False
        return True
    
    def _verifica_renavan (self,cr ,uid, ids, ctx=None):
        '''
        Função: Verifica repetições
        '''
        renavan = self.read(cr, uid, ids, ctx)[0]["renavam"]
        cr.execute(''' SELECT renavam FROM ud_transporte_veiculo WHERE renavam = '%s'  ''' % (renavan))
        result = cr.fetchall()
        if len(result) > 1:
            return False
        return True
    
    def _verifica_chassis (self, cr, uid, ids, ctx=None):
        '''
        Função: Verifica repetições
        '''
        chassis = self.read(cr, uid, ids, ctx)[0]["chassis"]
        cr.execute(''' SELECT chassis FROM ud_transporte_veiculo WHERE chassis = '%s'  ''' % (chassis))
        result = cr.fetchall()
        if len(result) > 1:
            return False
        return True
    
    _constraints = [(_verifica_placa, "Placa Duplicada", ["placa"]),(_verifica_renavan, "Renavan Duplicado", ["renavan"]), (_verifica_chassis, "Chassis Duplicado", ["chassis"])]
        
class transporte_manutencao(osv.osv):
    '''
    Nome: ud.transporte.manutencao
    descrição: Cadastro e acompanhamento de solicitações de manutenção
    '''
    _name = 'ud.transporte.manutencao'
    
    _columns = {
                'veiculo':fields.many2one('ud.transporte.veiculo', u'Veículo', required=True),
                'descricao_manutencao':fields.text(u'Descrição', required=True),
                'data_entrada':fields.date('Entrada', required=True),
                'data_saida':fields.date(u'Saída'),
                'custo_manutencao':fields.float('Custo'),
                'state':fields.selection(
                                        (('aberta',u'Aberta'),
                                        ('concluida',u'Concluída')),
                                        string='Status'
                                        ),
                }
    
    _defaults = {
                 'state':lambda *a:'aberta',
                 'data_entrada': fields.date.today(),
                 }
    def concluir(self, cr, uid, ids, context=None):
        '''
        Função: Conclui uma manutenção aberta
        '''
        return self.write(cr, uid, ids, {'state': 'concluida'})


class transporte_solicitacao(osv.osv):
    '''
    Nome: ud.transporte.solicitacao
    Descrição: Representa a solicitação e todo o processo de solicitacao
    '''
    _name = 'ud.transporte.solicitacao'
    _description = 'Solicitacao'
    
    conta_passageiros = lambda self, cr, uid, ids, field, args, context: self._conta_passageiros(cr, uid, ids,field,args, context)
    
    _columns = {
                'solicitante':fields.many2one('ud.employee',u'Solicitante',required=True,change_default=True, readonly=True),  
                'state':fields.selection([
                      ('aguardando','Aguardando'),
                      ('deferido','Deferido'),
                      ('deferidocomcusteio','Deferido com custeio'),
                      ('indeferido','Indeferido'),
                                          ],
                      'Status', required=True),
                'data_hora_saida':fields.datetime(u'Data de saída', required=True),
                'solicitante_email': fields.char('E-mail', size=240, change_default=True, readonly=True),
                'solicitante_telefone': fields.char('Telefone', size=10, required=True, change_default=True, readonly=True),
                'data_hora_chegada':fields.datetime(u'Previsão de chegada', required=True),
                'estado_saida':fields.selection([('ac', 'AC'), ('al', 'AL'), ('ap', 'AP'), ('am', 'AM'), ('ba','BA'), ('ce','CE'), ('df','DF'), ('es','ES'), ('go','GO'), ('ma','MA') , ('mg','MG'), ('ms','MS'), ('mt','MT'), ('pa','PA'), ('pe','PE'), ('pi','PI'), ('pr','PR'), ('rj','RJ'), ('rn','RN'), ('ro','RO'), ('rr','RR'), ('rs', 'RS'), ('sc','SC'), ('se','SE'), ('sp','SP'), ('to', 'TO')], 'Estado', required=True),
                'cidade_saida':fields.char( "Cidade", required=True),
                'rota': fields.text("Rota", required=False),
                'estado_destino':fields.selection([('ac', 'AC'), ('al', 'AL'), ('ap', 'AP'), ('am', 'AM'), ('ba','BA'), ('ce','CE'), ('df','DF'), ('es','ES'), ('go','GO'), ('ma','MA') , ('mg','MG'), ('ms','MS'), ('mt','MT'), ('pa','PA'), ('pe','PE'), ('pi','PI'), ('pr','PR'), ('rj','RJ'), ('rn','RN'), ('ro','RO'), ('rr','RR'), ('rs', 'RS'), ('sc','SC'), ('se','SE'), ('sp','SP'), ('to', 'TO')], 'Estado', required=True),
                'cidade_destino':fields.char( "Cidade", required=True),

                'objetivo':fields.text('Objetivo'),
                'qtd_passageiros':fields.function(conta_passageiros, string='Quantidade de passageiros', type="integer",method=True, required=True),

                'notas': fields.text('Notas'),
                'passageiros': fields.many2many("ud.transporte.passageiro","ud_transporte_passageiro_solicitacao",'vid','pid',string=u"Passageiros"),
                "rotulo": fields.text(u"Rótulo"),
                }
    _rec_name = "rotulo"
    
    _defaults = {  
        'state': lambda *a: 'aguardando',
        'solicitante': lambda self,cr,uid,context: self.recupera_usuario(cr,uid,context),
        'solicitante_telefone': lambda self,cr,uid,context: self.recupera_telefone(cr,uid,context),
        'solicitante_email': lambda self,cr,uid,context: self.recupera_email(cr,uid,context),
        }
    
    def onchange_passageiros (self, cr, uid, ids, passageiros):
        return {"value": {"qtd_passageiros": len(passageiros)}}
    
    def _conta_passageiros (self, cr, uid, ids,field,args, context):
        dados = self.browse(cr, uid, ids, context)[0]
        return {dados.id : len(dados.passageiros)}
    
    def create(self, cr, uid,values, context=None):
        '''
        Função: Reescrita osv.create()
        Descrição: Atribui um rotulo a solicitacao
        '''
        rotulo = u"Saída: %s, %s. Chegada %s, %s. " % (values['cidade_saida'], values['data_hora_saida'], values['cidade_destino'], values['data_hora_chegada'])
        values['rotulo'] = rotulo
        return super(osv.osv, self).create(cr,uid,values,context)
    
    def recupera_usuario (self, cr, uid, context=None):
        '''
        Função: _default
        Descrição: Localiza e preenche o usuário padrão
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
        
    def recupera_telefone (self, cr, uid, c):
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
        
    def recupera_email (self, cr, uid, c):
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
        
    # Botões
    def status_deferido(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'deferido'})
    def status_deferido_com_custeio(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'deferidocomcusteio'})
    def status_indeferido(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'indeferido'})
    
    def converteData(self, dataS):
        '''
        Função: Converte string em "datetime"
        '''
        partes_data = dataS[:10].split("-")
        partes_hora = dataS[11:].split(":")
        data = datetime(int(partes_data[0]),int(partes_data[1]),int(partes_data[2]),
                        int(partes_hora[0]),int(partes_hora[1]), int(partes_hora[2]))
        return data
    
    def _check_data_chegada(self, cr, uid, ids,context=None):
        '''
        Função: Verifica se a data de chegada é posterior a data de saída
        '''
        obj_solicitacao0 = self.read(cr,uid,ids,context=context)
        obj_solicitacao = obj_solicitacao0[0]
        solicitante_data_hora_chegada = obj_solicitacao["data_hora_chegada"]
        solicitante_data_hora_saida = obj_solicitacao["data_hora_saida"]
        dataSaidaOrdinal = self.converteData(solicitante_data_hora_saida)
        dataChegadaOrdinal = self.converteData(solicitante_data_hora_chegada)
        if (dataChegadaOrdinal <= dataSaidaOrdinal):
            return False
        return True
    
    _constraints = [
                    (_check_data_chegada, 'Erro! A data de previsão de chegada deve ser posterior a data de saída', ['solicitante_data_hora_saida']),
                    ]


class passageiro (osv.osv):
    '''
    Nome: ud.transporte.passageiro
    Descrição: Passageiro associado a viagem
    '''
    _name = 'ud.transporte.passageiro' 
    _columns = {
                'name':fields.char('Nome', required=True),
                'telefone':fields.char('Telefone', required=True),
                'cpf':fields.char('CPF'),
                'rg':fields.char('RG'), 
                }
    
class viagem (osv.osv):
    '''
    Nome: ud.transporte.viagem
    Descrição: Viagem realizada, associada a solicitação de viagem
    '''
    _name = 'ud.transporte.viagem'
    _columns = {
                'solicitacao_id':fields.many2one('ud.transporte.solicitacao','Solicitação', required=True, states={"concluida":[("readonly", True)]} ),
                'data_solicitacao':fields.datetime('Data de solicitação', states={"concluida":[("readonly", True)]}),
                'data_solicitacao_chegada':fields.datetime('Previsão de chegada', states={"concluida":[("readonly", True)]}),
                'motorista1': fields.many2one('ud.transporte.motorista', 'Motorista 1', required=True, states={"concluida":[("readonly", True)]}),
                'motorista2': fields.many2one('ud.transporte.motorista', 'Motorista 2', states={"concluida":[("readonly", True)]}),
                'veiculo': fields.many2one('ud.transporte.veiculo', 'Veículo', required=True, states={"concluida":[("readonly", True)]}),
                'custo':fields.float('Custo',help="Deixe em branco (0), caso seja sem custeio"),
                'abastecimento':fields.float('Abastecimento'),
                'preco_combustivel':fields.float('Preço do combustível'),
                'km_rodado':fields.integer('Km rodado', readonly=True),
                'state':fields.selection(
                      (('aberta', 'Aberta'),
                      ('concluida', 'Concluída')),
                     'Status da viagem'),
                'ocorrencia':fields.text('Ocorrências'),
                'notes': fields.text('Notas'),
                'km_inicial':fields.float('Km Inicial'),
                'km_final':fields.float('Km final'),
                "rotulo": fields.text("viagem"),
                }
    
    _defaults = {
                'state':lambda *a:'aberta',
                }
    
    _rec_name = "data_solicitacao"
    
    def onchange_solicitante(self, cr, uid, ids, name, context=None):
        res = {}
        obj_solicitacao = self.pool.get('ud.transporte.solicitacao').browse(cr,uid,name, context=context)

        res['data_solicitacao'] = obj_solicitacao.data_hora_saida
        res['data_solicitacao_chegada'] = obj_solicitacao.data_hora_chegada

        return {'value':res}
    
    def _formata_data (self, dataS):
        partes_data = dataS[:10].split("-")
        partes_hora = dataS[11:].split(":")
        data = datetime(int(partes_data[0]),int(partes_data[1]),int(partes_data[2]),
                        int(partes_hora[0]),int(partes_hora[1]), int(partes_hora[2]))
        return data
    
    def _verifica_veiculo (self, cr,uid, ids):
        viagem = self.read(cr, uid, ids)[0]
        data_desejada = self._formata_data(viagem["data_solicitacao"])
        cr.execute('''SELECT 
                          ud_transporte_viagem.data_solicitacao, 
                          ud_transporte_viagem.data_solicitacao_chegada
                        FROM 
                          public.ud_transporte_veiculo, 
                          public.ud_transporte_viagem
                        WHERE 
                          ud_transporte_veiculo.id = %s AND
                          ud_transporte_viagem.veiculo = ud_transporte_veiculo.id;
                    ''' % (viagem["veiculo"][0]))
        datas = cr.fetchall()
        if datas:
            if datas[0] != None:
                for data in datas:
                    data_saida = self._formata_data(data[0])
                    data_chegada = self._formata_data(data[1])
                    if data_saida < data_desejada < data_chegada:
                        return False
                return True
            
    def _verifica_motorista1 (self, cr ,uid, ids):
        viagem = self.read(cr, uid, ids)[0]
        data_desejada = self._formata_data(viagem["data_solicitacao"])
        cr.execute('''SELECT 
                          ud_transporte_viagem.data_solicitacao, 
                          ud_transporte_viagem.data_solicitacao_chegada
                        FROM 
                          public.ud_transporte_viagem, 
                          public.ud_transporte_motorista
                        WHERE 
                          ud_transporte_motorista.id = %s AND
                          ud_transporte_viagem.motorista1 = ud_transporte_motorista.id;
                    ''' % (viagem["motorista1"][0]))
        datas = cr.fetchall()
        if datas:
            if datas[0] != None:
                for data in datas:
                    data_saida = self._formata_data(data[0])
                    data_chegada = self._formata_data(data[1])
                    if data_saida < data_desejada < data_chegada:
                        return False
                return True

    def _verifica_motorista2 (self, cr ,uid, ids):
        viagem = self.read(cr, uid, ids)[0]
        data_desejada = self._formata_data(viagem["data_solicitacao"])
        if viagem["motorista2"] and viagem["motorista2"] == None:
            cr.execute('''SELECT 
                              ud_transporte_viagem.data_solicitacao, 
                              ud_transporte_viagem.data_solicitacao_chegada
                            FROM 
                              public.ud_transporte_viagem, 
                              public.ud_transporte_motorista
                            WHERE 
                              ud_transporte_motorista.id = %s AND
                              ud_transporte_viagem.motorista1 = ud_transporte_motorista.id;
                        ''' % (viagem["motorista2"][0]))
            datas = cr.fetchall()
            if datas:
                if datas[0] != None:
                    for data in datas:
                        data_saida = self._formata_data(data[0])
                        data_chegada = self._formata_data(data[1])
                        if data_saida < data_desejada < data_chegada:
                            return False
                    return True
        return True
    
    _constraints = [
                    (_verifica_veiculo, "Veículo em uso neste período", ["data_solicitacao"]), 
                    (_verifica_motorista1, "Existe viagem agendada para esse motorista nesse período", ["motorista1"]),
                    (_verifica_motorista2, "Existe viagem agendada para esse motorista nesse período", ["motorista2"]),
                    ]
    
    _sql_constraints = [("solicitacao_uniq", "unique(solicitacao_id)", "Só é permitido uma viagem por solicitação")]