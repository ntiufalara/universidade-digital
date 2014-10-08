#coding: utf-8
import datetime
import logging
import re
import time
from types import NoneType

from account.account import _logger
import addons
from hr.hr import hr_employee
from osv import fields, osv


class ud_campus(osv.osv):
    '''
        Classe que representa os campos do formulário Campus.
        
    '''
    _name = 'ud.campus'
    _description = "Campus"

    _columns = {
        'name': fields.char('Nome', size=40, required=True, help="Ex.: Arapiraca, Sertão, Litoral etc."),
        'description':fields.text('Descrição'),
        'diretor': fields.many2one('ud.employee', 'Diretor', ondelete='cascade'),
        'diretor_acad': fields.many2one('ud.employee', 'Diretor Acadêmico', ondelete='cascade'),
        
        'is_active': fields.boolean('Ativo?'),
    }
    
ud_campus()

class ud_espaco (osv.osv):
    _name    = 'ud.espaco'
    _columns = {
                'name':fields.char('Nome', size=80, required=True),
                'capacidade': fields.integer('Capacidade', required=True, help="Número de pessoas."), #depois trocar para inteiro
                'permite_reserva': fields.boolean('Permitir Reserva'),
                'local_polo':fields.many2one('ud.polo','Polo', required=True, ondelete='cascade'),
                'local_bloco_polo':fields.many2one('ud.bloco', 'Bloco', required=True, ondelete='cascade'),
                'informacoes_adicionais':fields.text('Descrição'),
               
                }
    
    def limpa_bloco(self, cr, uid, ids):
        campos = ["local_bloco_polo"]
        valores = {}
        for campo in campos:
            valores[campo] = ""
        print valores
        return {'value':valores}
    
    
ud_espaco()
    


class ud_polo(osv.osv):
    '''
        Classe que representa os campos do formulário Pólo.
        
    '''
    _name = 'ud.polo'
    _description = "Polo"

    _columns = {
        'name': fields.char('Nome', size=80, required=True, help="Ex.: Viçosa, Penedo, Palmeira etc."),
	    'campus_id':fields.many2one('ud.campus', 'Campus', required=True),       
		#'is_sede': fields.boolean('Sede?'),
		'localizacao': fields.char('Endereço', size=120),
		'is_active': fields.boolean('Ativo?'),
        'descricao': fields.text('Descrição'),
        'bloco_ids': fields.one2many('ud.bloco', 'ud_bloco_ids', 'Bloco', ondelete='cascade'),
        
        
	}
    
    
ud_polo()

class ud_bloco(osv.osv):
    
    _name = 'ud.bloco'
    _description = 'Bloco'
    
    _columns = {
        'name': fields.char('Bloco', size=80, required=True),
        'ud_bloco_ids': fields.many2one('ud.polo', 'Polo', ondelete='cascade', invisible=True),
                 
    }
ud_bloco()


    

class ud_setor(osv.osv):
    '''
        Classe que representa os campos do formulário Setor.
        
    '''
    _name = 'ud.setor'
    _description = 'Setor'
    
    _columns = {
            'name': fields.char('Nome', size=80, required=True),
            'descricao': fields.text('Descrição'),
            'polo_id': fields.many2one('ud.polo', 'Polo',required=True, ondelete='cascade'),
            'is_active': fields.boolean('Ativo?'),
                           
    }
    
    

    
ud_setor()


class ud_curso(osv.osv):
    '''
        Classe que representa os campos do formulário Curso.
    '''    
    _name = 'ud.curso'
    _description = 'Curso'
    
    

    _columns = {
        		'name': fields.char('Nome', size=40, help="Ex.: Ciência da Computação",required=True),
                'polo_id':fields.many2one('ud.polo', 'Polo',ondelete='cascade',required=True),
        		'coordenador': fields.many2one('ud.employee','Coordenador', ondelete='cascade'),
                'is_active': fields.boolean('Ativo?'),
                'description': fields.text('Descrição'),
                'disciplina_ids': fields.one2many('ud.disciplina', 'ud_disc_id', 'Disciplina', ondelete='cascade'), 
    }    

    
ud_curso()

class ud_disciplina(osv.osv):
    '''
        Classe que representa os campos do formulário Disciplina (Associada com a classe Curso).
        
    '''
    _name = 'ud.disciplina'
    _description = 'Disciplina'
    
    _columns = {
            'codigo': fields.char('Código', size=15, required=True),
            'name': fields.char('Nome', size=40, required=True),
            'ch': fields.char('Carga Horária', size=10, required=True),
            'descricao': fields.text('Descrição'),
            'ud_disc_id': fields.many2one('ud.curso', 'Curso:', ondelete='cascade', invisible=True),
                               
    }
    
ud_disciplina()


class ud_papel(osv.osv): #Classe papel
    '''
        Classe que representa os campos do formulário Papéis (Associada a classe ud_employee).
        
    '''
    _name = 'ud.perfil'
    _description = 'Papel'
    

    _columns = {
        'tipo': fields.selection((('p','Docente'), ('t','Técnico'), ('a','Discente'), ('x','Terceirizado'), ('o', 'Outra')),'Tipo', required=False),
        'is_bolsista':fields.boolean('Bolsista'),
        'tipo_bolsa': fields.selection((('per', 'Permanência'), ('pai', 'Painter'), ('pibic', 'PIBIC-CNPq'), ('pibip', 'PIBIB-Ação'), ('pibit', 'PIBIT-CNPq'), ('aux', 'Auxílio Alimentação'), ('aux_t', 'Auxílio Transporte'), ('bdi','BDI'), ('bdai', 'BDAI'),('pibid','PIBID'), ('m', 'Monitoria')), 'Tipo de Bolsa'),
        'valor_bolsa':fields.char(u"Valor da Bolsa (R$)", size=7),
        
        'tipo_docente': fields.selection((('pa', 'Professor Assistente'), ('pad', 'Professor Adjunto'), ('pt', 'Professor Titular')),'Tipo de Docente'),
        'matricula': fields.char('Matricula', size=15, help="Ex.: 123456789", required=True),
        'data_validade': fields.date('Data de Validade'),
        'ud_papel_id': fields.many2one('ud.employee', 'Papel', ondelete='cascade', invisible=True),
        'ud_cursos': fields.many2one('ud.curso','Curso', ondelte='cascade'),
        'ud_setores': fields.many2one('ud.setor', 'Setor', ondelete='cascade'),
    }
    
    def _setor_ou_curso(self, cr, uid, ids, context=None):
        '''
            Método que valida a entrada de Setor ou Curso (sem deixá-los em branco).
            :return False se os campos estão em branco ou True, caso contrário.
        '''       
        obj_setor_curso = self.pool.get('ud.perfil').browse(cr, uid, ids, context=context)
        
        for data in obj_setor_curso:
            if not data.ud_setores and not data.ud_cursos:
                return False        
        return True
        
    _sql_constraints = [
        ('papel_uniq', 'unique (matricula,tipo)', u'A matrícula já cadastrada para esse tipo de papel.'),
    ]
    
    _constraints = [(_setor_ou_curso, 'Preencha pelo menos um dos campos.', ['Setor', 'Curso'])]
    
    
ud_papel()

class ud_dado_bancario(osv.osv):
    '''
        Classe que representa os campos do formulário Dados Bancários (Associada a classe ud_employee).
                
    '''
    _name = 'ud.dados'
    _description = 'Dados Bancários'
    _columns = {
        'banco': fields.selection((('218','218 - Banco Bonsucesso S.A.'), ('36','036 - Banco Bradesco BBI S.A'), ('204','204 - Banco Bradesco Cartões S.A.'), ('237','237 - Banco Bradesco S.A.'), ('263','263 - Banco Cacique S.A.'), ('745','745 - Banco Citibank S.A.'), ('229','229 - Banco Cruzeiro do Sul S.A.'), ('1','001 - Banco do Brasil S.A.'), ('47','047 - Banco do Estado de Sergipe S.A.'), ('37','037 - Banco do Estado do Pará S.A.'), ('41','041 - Banco do Estado do Rio Grande do Sul S.A.'), ('4', '004 - Banco do Nordeste do Brasil S.A.'), ('184', '184 - Banco Itaú BBA S.A.'), ('479','479 - Banco ItaúBank S.A'), ('479A','479A - Banco Itaucard S.A.'), ('M09','M09 - Banco Itaucred Financiamentos S.A.'), ('389','389 - Banco Mercantil do Brasil S.A.'),('623','623 - Banco Panamericano S.A.'),('633','633 - Banco Rendimento S.A.'),('453','453 - Banco Rural S.A.'),('422','422 - Banco Safra S.A.'),('33', '033 - Banco Santander (Brasil) S.A.'),('73', '073 - BB Banco Popular do Brasil S.A.'),('104','104 - Caixa Econômica Federal'),('477', '477 - Citibank N.A.'),('399','399 - HSBC Bank Brasil S.A. – Banco Múltiplo'), ('652', '652 - Itaú Unibanco Holding S.A.'),('341','341 - Itaú Unibanco S.A.'),('409','409 - UNIBANCO – União de Bancos Brasileiros S.A.')), 'Banco', required=True),
        'agencia': fields.char(u'Agência', size=5, required=True),
        'conta' : fields.char('Conta', size=6, required=True),
        'tipo_conta': fields.selection((('c', 'Conta Corrente'), ('p', 'Conta Poupança')), 'Tipo', required=True),
        'ud_conta_id': fields.many2one('ud.employee', u'Dados Bancários', invisible=True),
                 
    }
    
    def _valida_conta_bancaria(self, cr, uid, ids, context=None):
        '''
            Método que valida os campos do formulário Dados Bancários. Ex.: Conta:111111 (sem traços).
            return: False se dados passados estão fora desse padrão ou True, caso contrário.
        
        '''
        record = self.browse(cr, uid, ids, context=None)
        for data in record:
            if len(data.conta) != 6:
                return False
            else:
                try:                   
                    if type(re.match("^-?[0-9]+$", data.conta[0:7])) != NoneType:
                        return True
                    else:
                        return False
                except:
                    return False           
        return True
    
    def _valida_agencia(self, cr, uid, ids, context=None):
        '''
            Método que valida os campos do formulário Dados Bancários. Ex.: Agência:1111X (sem traços).
            return: False se dados passados estão fora desse padrão ou True, caso contrário.
        
        '''
        record = self.browse(cr, uid, ids, context=None)
        for data in record:
            if len(data.agencia) != 5:
                return False
            else: 
                try:                   
                    if type(re.match("^-?[0-9]+$", data.agencia[0:4])) != NoneType:
                        return True
                    else:
                        return False
                except:
                    return False        
        return True
    
    _constraints = [(_valida_conta_bancaria, "Código de conta inválido.", ['Conta']), (_valida_agencia, "Código de agência inválido.", ['Agencia'])]
    
ud_dado_bancario()

class ud_employee(osv.osv):
    '''
        Classe que representa os campos do formulário Pessoa.
    '''          
    _name = "ud.employee"
    
    _description = "Employee"
    _inherits = {'res.users': "user_id", 'mail.alias':"alias_id"}
    _columns = {
        #'login': fields.related('user_id', 'login', type='char', string='Login', readonly=0),
        #'password': fields.related('user_id', 'password', type='char', string='Senha', readonly=0),
        'user_id': fields.many2one('res.users', "Usuário", ondelete='cascade'),
        'last_login': fields.related('user_id', 'date', type='datetime', string='Latest Connection', readonly=1),
        'alias_id': fields.related('alias_id', 'alias', type='char', string='alias', readonly=0),
        #'country_id': fields.many2one('res.country', 'Nacionalidad:'),
        'birthday': fields.date("Data de Nascimento", required=False),
        'gender': fields.selection([('masculino', 'Masculino'),('feminino', 'Feminino')], u'Gênero', required=False),
        'marital': fields.selection([('solteiro', 'Solteiro'), ('casado', 'Casado'), ('viuvo', 'Viúvo'), ('divorciado', 'Divorciado')], 'Estado Civil',required=False),
        #'department_id':fields.many2one('hr.department', 'Departamento'),
        #'address_id': fields.many2one('res.partner', 'Endereço comercial'),
       # 'address_home_id': fields.many2one('res.partner', 'Endereço'),
        #'partner_id': fields.related('address_home_id', 'partner_id', type='many2one', relation='res.partner', readonly=True, help="Partner that is related to the current employee. Accounting transaction will be written on this partner belongs to employee."),
        'work_phone': fields.char('Telefone Fixo', size=32),
        'mobile_phone': fields.char('Celular', size=32, required=False),
        'work_email': fields.char(u'E-mail', size=240, required=False),
        'notes': fields.text('Notas'),
        #'parent_id': fields.many2one('ud.employee', 'Gerenciador'),
        #'child_ids': fields.one2many('ud.employee', 'parent_id', 'Subordinates'),
        'photo': fields.binary('Foto'),        
        # Adicionados por mim
        'cpf':fields.char('CPF', size=14, required=True, help="Entre o CPF no formato: XXX.XXX.XXX-XX"),
        'rg':fields.char('RG', size=20, required=False),
        'orgaoexpedidor':fields.char(u'Orgão Expedidor', size=8, help="Sigla: Ex. SSP/SP", required=False),
        'papel_ids': fields.one2many('ud.perfil', 'ud_papel_id', 'Papel', ondelete='cascade'),
        'dados': fields.one2many('ud.dados', 'ud_conta_id', u'Dados Bancários'),
        'nacionalidade': fields.selection((('al','Alemã'),('es','Espanhola'),('fr','Francesa'),('gr','Grega'),('hu','Húngaro'),('ir', 'Irlandesa'), ('it','Italiana'), ('ho','Holandesa'), ('pt','Portuguesa'), ('in','Inglesa'), ('rs', 'Russa'), ('ar','Argentina'), ('br', 'Brasileira'), ('ch','Chilena'), ('eu', 'Norte-Americana'), ('mx', 'Mexicana'),('chi', 'Chinesa'),('jp', 'Japonesa'),('sf','Sul-Africana'),('as','Australiana')),'Nacionalidade',required=False),
        'endereco': fields.char(u'Endereço', size=120, required=False),
        'bairro': fields.char('Bairro', size=32, required=False),
        'endereco_com': fields.char('Cidade', size=120, required=False),
        'estado': fields.selection([('ac', 'AC'), ('al', 'AL'), ('ap', 'AP'), ('am', 'AM'), ('ba','BA'), ('ce','CE'), ('df','DF'), ('es','ES'), ('go','GO'), ('ma','MA') , ('mg','MG'), ('ms','MS'), ('mt','MT'), ('pa','PA'), ('pe','PE'), ('pi','PI'), ('pr','PR'), ('rj','RJ'), ('rn','RN'), ('ro','RO'), ('rr','RR'), ('rs', 'RS'), ('sc','SC'), ('se','SE'), ('sp','SP'), ('to', 'TO')], 'Estado', required=True),
    }
    
    

    def _valida_cpf(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        cpf = self.read(cr, uid, ids, ["cpf"], context = context, load = "_classic_write")[0].get("cpf")
        cpf = str(cpf).replace(".", "").replace("-", "")
        if any([not cpf, not cpf.isdigit(), len(cpf) < 11, cpf.count(cpf[0]) == 11]):
            return False
        dv = cpf[-2:]
        cpf = map(lambda num: int(num), cpf[:-2])
        # Funções
        seq = lambda max: zip([n for n in range(max, 1, -1)], cpf)
        resto = lambda lista: sum(map(lambda g: g[0]*g[1], lista))%11
        dig_verif = lambda valor: 0 if valor < 2 else 11 - valor
          
        cpf.append(dig_verif(resto(seq(10))))
        cpf.append(dig_verif(resto(seq(11))))
        if dv[0] != str(cpf[-2]) or dv[1] != str(cpf[-1]):
            return False
        return True
    
    

    
    def _cria_usuario(self, cr, uid, ids, context=None):
        name = self.browse(cr,uid, ids)[0].name
        cpf = self.browse(cr,uid, ids)[0].cpf[0:3]
        cr.execute('''INSERT INTO res_users (login, password, company_id, partner_id, alias_id, write_uid, menu_id, create_uid) VALUES ('%s', '%s', '1', '3', '1', '1', '1', '1');'''% (name, cpf))
        return True
    
    
    def _valida_rg(self, cr, uid, ids, context=None):
        '''
            Método que valida os campos do formulário Pessoa. Ex.: RG:111111 (sem traços).
            return: False se dados passados estão fora desse padrão ou True, caso contrário.
        
        '''
        record = self.browse(cr, uid, ids, context=None)
        for data in record:
            if type(re.match("^-?[0-9]+$", data.rg)) != NoneType:
                return True
        else:
            return False
        return True
    
    def _valida_email(self, cr, uid, ids, context=None):
        '''
            Método que valida os campos do formulário Pessoa. Ex.: RG:111111 (sem traços).
            return: False se dados passados estão fora desse padrão ou True, caso contrário.
        
        '''
        record = self.browse(cr, uid, ids, context=None)
        for data in record:
            if type(re.match("(?:^|\s)[-a-z0-9_.]+@(?:[-a-z0-9]+\.)+[a-z]{2,6}(?:\s|$)",data.work_email)) != NoneType:
                return True
        else:
            return False
        return True
    
    
    def _valida_telefone(self, cr, uid, ids, context=None):
        '''
            Método que valida os campos do formulário Pessoa. Ex.: Telefone Residencial:111111 (somente números).
            return: False se dados passados estão fora desse padrão ou True, caso contrário.
        
        '''
        record = self.browse(cr, uid, ids, context=None)
        try:
            for data in record:
                if type(re.match("^-?[0-9]+$", data.work_phone)) != NoneType:
                    return True
            else:
                return False
        except TypeError:
            pass
        return True
    
    def _valida_celular(self, cr, uid, ids, context=None):
        '''
            Método que valida os campos do formulário Pessoa. Ex.: Telefone Celular:111111 (somente números).
            return: False se dados passados estão fora desse padrão ou True, caso contrário.
        
        '''
        record = self.browse(cr, uid, ids, context=None)
        for data in record:
            if type(re.match("^-?[0-9]+$", data.mobile_phone)) != NoneType:
                return True
            else:
                return False
        return True    
    
    def _checar_data_nascimento(self, cr, uid, ids, context=None):
        '''
            Método que verifica se a Pessoa é maior de 18 anos.
            return: False se a pessoa tiver idade menor que 18 anos ou True, caso contrário.
        '''
        obj_data_employee = self.pool.get('ud.employee').browse(cr, uid, ids)
        for obj in obj_data_employee:
            data_nascimento = datetime.datetime.strptime(obj.birthday, "%Y-%m-%d").date()
            if datetime.date.today().year - data_nascimento.year < 18:
                return False
        return True       

    

    def _get_photo(self, cr, uid, context=None):
        photo_path = addons.get_module_resource('hr','images','hr.png')
        return open(photo_path, 'rb').read().encode('base64')

    
    
    def _obrigar_papel(self, cr, uid, ids, context=None):
        obj_papel = self.pool.get('ud.employee').browse(cr, uid, ids, context=context)
        
        for data in obj_papel:
            if not data.papel_ids:
                return False
        return True
    
    _constraints = [
        (_obrigar_papel, 'Pessoa precisa ter pelo menos um papel.', [u'Papéis']),
        (_valida_cpf, u"CPF inválido.", ["\nCPF"]),
        (_valida_email, u"E-mail inválido.", ["E-mail"]),
        
        
    ]
    
    _defaults = {
        'photo': _get_photo,
        'marital': 'solteiro',
        'nacionalidade': 'br'
    }
    
    _sql_constraints = [('ud_cpf_uniq', 'unique(cpf)',u'Já existe CPF com esse número cadastrado.'),('ud_rg_uniq','unique(rg)',u'Já existe RG com esse número cadastrado.')]

ud_employee()
