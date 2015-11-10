#coding: utf-8
import re
from types import NoneType

from openerp.modules.module import get_module_resource
from openerp.osv import osv, fields
import openerp.tools as tools
import addons




ID_CONTA_ADMIN = 1

#Tupla que guarda a lista dos principais bancos.
_BANCOS = [('218', u'218 - Banco Bonsucesso S.A.'),
           ('36', u'036 - Banco Bradesco BBI S.A'),
           ('204', u'204 - Banco Bradesco Cartões S.A.'),
           ('237', u'237 - Banco Bradesco S.A.'),
           ('263', u'263 - Banco Cacique S.A.'),
           ('745', u'745 - Banco Citibank S.A.'),
           ('229', u'229 - Banco Cruzeiro do Sul S.A.'),
           ('1', u'001 - Banco do Brasil S.A.'),
           ('47', u'047 - Banco do Estado de Sergipe S.A.'),
           ('37', u'037 - Banco do Estado do Pará S.A.'),
           ('41', u'041 - Banco do Estado do Rio Grande do Sul S.A.'),
           ('4', u'004 - Banco do Nordeste do Brasil S.A.'),
           ('184', u'184 - Banco Itaú BBA S.A.'),
           ('479', u'479 - Banco ItaúBank S.A'),
           ('479A', u'479A - Banco Itaucard S.A.'),
           ('M09', u'M09 - Banco Itaucred Financiamentos S.A.'),
           ('389', u'389 - Banco Mercantil do Brasil S.A.'),
           ('623', u'623 - Banco Panamericano S.A.'),
           ('633', u'633 - Banco Rendimento S.A.'),
           ('453', u'453 - Banco Rural S.A.'),
           ('422', u'422 - Banco Safra S.A.'),
           ('33', u'033 - Banco Santander (Brasil) S.A.'),
           ('73', u'073 - BB Banco Popular do Brasil S.A.'),
           ('104', u'104 - Caixa Econômica Federal'),
           ('477', u'477 - Citibank N.A.'),
           ('399', u'399 - HSBC Bank Brasil S.A. – Banco Múltiplo'),
           ('652', u'652 - Itaú Unibanco Holding S.A.'),
           ('341', u'341 - Itaú Unibanco S.A.'),
           ('409', u'409 - UNIBANCO – União de Bancos Brasileiros S.A.'),
           ]

class ud_banco(osv.osv):
    '''
    Classe que representa a entidade Banco.
    '''
    _name = "ud.banco"
    _description = u'Configurações das informações bancárias'
    _order = "banco asc"
    
    _columns = {
        "banco": fields.selection(_BANCOS, u"Banco", required=True),
        "agencia": fields.boolean(u"Agência"),
        "dv_agencia": fields.boolean(u"DV da Agência", help=u"Dígito verificador da agência"),
        "conta": fields.boolean(u"Conta"),
        "dv_conta": fields.boolean(u"DV da Conta", help=u"Dígito verificador da conta"),
        "operacao": fields.boolean(u"Operação", help=u"Tipo de conta"),
    }
    
    _defaults = {
        'agencia': True,
        'conta': True,
        'dv_conta': True,
    }
    
    _sql_constraints = [
        ('banco_uniq', 'unique (banco)', u"Não é permitido cadastrar mais de um banco!"),
    ]
    
    def name_get(self, cr, uid, ids, context=None):
        '''
        Retorna os dados do banco a aprtir do seu nome.
        '''
        if isinstance(ids, (int, long)):
            ids = [ids]
        bancos = dict(_BANCOS)
        result = []
        for banco in self.read(cr, uid, ids, ["banco"], context=context, load="_classic_write"):
            result.append((banco.get("id"), bancos.get(banco.get("banco"))))
        return result

ud_banco()


class ud_dados_bancarios(osv.osv):
    '''
    Classe que representa a entidade Dados Bancários.
    '''
    _name = "ud.dados.bancarios"
    _description = u"Dados bancários"
    
    def _visibilidade(self, cr, uid, ids, field, arg, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        result = {}.fromkeys(ids, False)
        banco_model = self.pool.get("ud.banco")
        field = field.replace("_v", "")
        for dado in self.read(cr, uid, ids, ["banco_id"], context=context, load="_classic_write"):
            banco = banco_model.read(cr, uid, dado.get("banco_id"), [field], context=context, load="_classic_write")
            if dado:
                result[dado.get("id")] = banco.get(field)
        return result
    
    def _update_dados_bancarios(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        return ids
    
    _columns = {
        "banco_id": fields.many2one("ud.banco", u"Banco", required=True, ondelete = "restrict"),
        "agencia": fields.char(u"Agência", size=4, help=u"Número da Agência"),
        "dv_agencia": fields.char(u"DV Agência", size=2, help=u"Dígito verificador da Agência"),
        "conta": fields.char(u"Conta", size=10, help=u"Número da Conta"),
        "dv_conta": fields.char(u"DV Conta", size=1, help=u"Dígito verificador da Conta"),
        "operacao": fields.char(u"Operação", size=3, help=u"Tipo de conta"),
        
        "ud_conta_id": fields.many2one("ud.employee", u"Proprietário", invisible=False),
        
        "agencia_v": fields.function(_visibilidade, type = "boolean", method = True, invisible=True,
                                     store = {"ud.dados.bancarios": (_update_dados_bancarios, ["banco_id"], 15)}),
        "dv_agencia_v": fields.function(_visibilidade, type = "boolean", method = True, invisible=True,
                                     store = {"ud.dados.bancarios": (_update_dados_bancarios, ["banco_id"], 15)}),
        "conta_v": fields.function(_visibilidade, type = "boolean", method = True, invisible=True,
                                     store = {"ud.dados.bancarios": (_update_dados_bancarios, ["banco_id"], 15)}),
        "dv_conta_v": fields.function(_visibilidade, type = "boolean", method = True, invisible=True,
                                     store = {"ud.dados.bancarios": (_update_dados_bancarios, ["banco_id"], 15)}),
        "operacao_v": fields.function(_visibilidade, type = "boolean", method = True, invisible=True,
                                     store = {"ud.dados.bancarios": (_update_dados_bancarios, ["banco_id"], 15)}),
    }
    
    def name_get(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        bancos = dict(_BANCOS)
        result = []
        for banco in self.browse(cr, uid, ids, context=context):
            result.append((banco.id, bancos.get(banco.banco_id.banco)))
        return result
    
    def onchange_banco(self, cr, uid, ids, campo, context=None):
        banco = self.pool.get("ud.banco").read(cr, uid, campo, ["agencia", "dv_agencia", "conta", "dv_conta",
                                                                         "operacao"], context=context, load="_classic_write")
        if banco:
            value = {}
            for dado in banco.keys():
                value["%s_v" %dado] = banco.get(dado)
                if not banco.get(dado):
                    value[dado] = None
            return {"value": value}
        return {"value": {"agencia_v": False, "dv_agencia_v": False, "conta_v": False, "dv_conta_v": False,"operacao_v": False,
                          "agencia": None, "dv_agencia": None, "conta": None, "dv_conta": None, "operacao": None}}

ud_dados_bancarios()




class ud_campus(osv.osv):
    '''
        Classe que representa os campos do formulário Campus.
        
    '''
    _name = 'ud.campus'
    _description = "Campus"

    _columns = {
        'name': fields.char(u'Nome', size=40, required=True, help=u"Ex.: Arapiraca, Sertão, Litoral etc."),
        'description':fields.text(u'Descrição'),
        'diretor': fields.many2one(u'ud.employee', u'Diretor', ondelete='cascade'),
        'diretor_acad': fields.many2one(u'ud.employee', u'Diretor Acadêmico', ondelete='cascade'),
        
        'is_active': fields.boolean(u'Ativo?'),
    }
    
ud_campus()

class ud_espaco (osv.osv):
    '''
    Classe que representa a entidade Espaço.
    '''
    _name    = 'ud.espaco'
    _columns = {
                'name':fields.char(u'Nome', size=80, required=True),
                'capacidade': fields.integer(u'Capacidade', required=True, help=u"Número de pessoas."), #depois trocar para inteiro
                'permite_reserva': fields.boolean(u'Permitir Reserva'),
                'local_polo':fields.many2one('ud.polo',u'Polo', required=True, ondelete='cascade'),
                'local_bloco_polo':fields.many2one('ud.bloco', u'Bloco', required=True, ondelete='cascade'),
                'informacoes_adicionais':fields.text(u'Descrição'),
               
                }
    
    def limpa_bloco(self, cr, uid, ids):
        '''
            Limpa o campo bloco se o polo não pertencer a ele.
        '''
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
    _description = u"Polo"

    _columns = {
        'name': fields.char(u'Nome', size=80, required=True, help=u"Ex.: Viçosa, Penedo, Palmeira etc."),
        'campus_id':fields.many2one('ud.campus', u'Campus', required=True),       
        #'is_sede': fields.boolean('Sede?'),
        'localizacao': fields.char(u'Endereço', size=120),
        'is_active': fields.boolean(u'Ativo?'),
        'descricao': fields.text(u'Descrição'),
        'bloco_ids': fields.one2many('ud.bloco', 'ud_bloco_ids', u'Bloco', ondelete='cascade'),
        
        
    }
    
    
ud_polo()

class ud_bloco(osv.osv):
    '''
        Classe que representa os campos do formulário Bloco.
        
    ''' 
    _name = 'ud.bloco'
    _description = u'Bloco'
    
    _columns = {
        'name': fields.char(u'Bloco', size=80, required=True),
        'ud_bloco_ids': fields.many2one('ud.polo', u'Polo', ondelete='cascade', invisible=True),
    }
    
    _order = "name"
    
ud_bloco()

class ud_projeto(osv.osv):
    '''
        Classe que representa os campos do formulário Projeto.
        
    '''
    _name = 'ud.projeto'
    _description = u'Projeto'


    _columns = {
            'name': fields.char(u'Nome', size=40,required=True),
            'curso_id':fields.many2one('ud.curso', u'Cursos',ondelete='cascade',invisible=True),
            'data_inicio': fields.date(u'Data de inicio'),
            'data_fim': fields.date(u'Data Final (Prevista)'),
            'detalhes': fields.text(u'Descrição'),
            #'bolsistas': fields.many2one('ud.employee.nae', string='Bolsistas'), # ATENÇÃO: REFERENCIA CRUZADA: Quando for implantar no servidor, será necessário comentar essa linha. Após as tabelas terem sido criadas, descomentar.
    }
ud_projeto()


    

class ud_setor(osv.osv):
    '''
        Classe que representa os campos do formulário Setor.
        
    '''
    _name = 'ud.setor'
    _description = u'Setor'
    
    _columns = {
            'name': fields.char(u'Nome', size=80, required=True),
            'descricao': fields.text(u'Descrição'),
            'polo_id': fields.many2one('ud.polo', u'Polo',required=True, ondelete='cascade'),
            'sigla': fields.char(u'Sigla', size=50, required=True),
            'is_active': fields.boolean(u'Ativo?'),
                           
    }
    
    

    
ud_setor()


class ud_curso(osv.osv):
    '''
        Classe que representa os campos do formulário Curso.
    '''    
    _name = 'ud.curso'
    _description = u'Curso'
    
    

    _columns = {
                'name': fields.char(u'Nome', size=40, help=u"Ex.: Ciência da Computação",required=True),
                'polo_id':fields.many2one('ud.polo', u'Polo',ondelete='cascade',required=True),
                'coordenador': fields.many2one('ud.employee',u'Coordenador', ondelete='cascade'),
                'is_active': fields.boolean(u'Ativo?'),
                'description': fields.text(u'Descrição'),
                'disciplina_ids': fields.one2many('ud.disciplina', 'ud_disc_id', u'Disciplina', ondelete='cascade'),
                'projeto_ids': fields.one2many('ud.projeto','curso_id', u'Projetos', ondelete='cascade'), 
    }    

    
ud_curso()

class ud_disciplina(osv.osv):
    '''
        Classe que representa os campos do formulário Disciplina (Associada com a classe Curso).
        
    '''
    _name = 'ud.disciplina'
    _description = u'Disciplina'
    
    _columns = {
            'codigo': fields.char(u'Código', size=15, required=True),
            'name': fields.char(u'Nome', size=40, required=True),
            'ch': fields.char(u'Carga Horária', size=10, required=True),
            'descricao': fields.text(u'Descrição'),
            'ud_disc_id': fields.many2one('ud.curso', u'Curso', ondelete='cascade', invisible=True),
                               
    }
    
ud_disciplina()


class ud_papel(osv.osv): #Classe papel
    '''
        Classe que representa os campos do formulário Papéis (Associada a classe ud_employee).
        
    '''
    _name = 'ud.perfil'
    _description = 'Papel'
    

    _columns = {
        'tipo': fields.selection((('p',u'Docente'), ('t',u'Técnico'), ('a',u'Discente'), ('x',u'Terceirizado'), ('o', u'Outra')),u'Tipo', required=False),
        'is_bolsista':fields.boolean(u'Bolsista'),
        'tipo_bolsa': fields.selection((('per', u'Permanência'), ('pai', u'Painter'), ('pibic', u'PIBIC-CNPq'), ('pibip', u'PIBIB-Ação'), ('pibit', u'PIBIT-CNPq'), ('aux', u'Auxílio Alimentação'), ('aux_t', u'Auxílio Transporte'), ('bdi',u'BDI'), ('bdai', u'BDAI'),('pibid',u'PIBID'), ('m', u'Monitoria')), u'Tipo de Bolsa'),
        'valor_bolsa':fields.char(u"Valor da Bolsa (R$)", size=7),
        
        'tipo_docente': fields.selection((('pa', u'Professor Assistente'), ('pad', u'Professor Adjunto'), ('pt', u'Professor Titular')),u'Tipo de Docente'),
        'matricula': fields.char(u'Matricula', size=15, help=u"Ex.: 123456789", required=True),
        'data_validade': fields.date(u'Data de Validade'),
        'ud_papel_id': fields.many2one('ud.employee', u'Papel', ondelete='cascade', invisible=True),
        'ud_cursos': fields.many2one('ud.curso',u'Curso', ondelte='cascade'),
        'ud_setores': fields.many2one('ud.setor', u'Setor', ondelete='cascade'),
        'ud_projetos': fields.many2one('ud.projeto', u'Setor', ondelete='cascade')
    }
    
    _rec_name = "matricula"
    
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
        ('papel_uniq', 'unique (matricula,tipo)', u'Matricula já cadastrada para esse tipo de papel.'),
    ]
    
    _constraints = [(_setor_ou_curso, u'Preencha pelo menos um dos campos.', ['Setor', 'Curso'])]
    
    
ud_papel()


class ud_employee(osv.osv):
    
    '''
        Classe que representa os campos do formulário Pessoa.
    '''          
    _name = "ud.employee"
    
    _description = u"Employee"
    
    _inherits = {'resource.resource': 'resource_id'}
    
    def _get_image(self, cr, uid, ids, name, args, context=None):
        '''
         Retorna a imagem redimensionada.
        '''
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            result[obj.id] = tools.image_get_resized_images(obj.image)
        return result
    
    def _set_image(self, cr, uid, id, name, value, args, context=None):
        '''
         Seta a imagem.
        '''
        return self.write(cr, uid, [id], {'image': tools.image_resize_image_big(value)}, context=context)
    
    _columns = {
        u'user_id' : fields.many2one('res.users', u'Conta de Usuário', help=u'Related user name for the resource to manage its access.', ondelete='cascade'),
	u'curriculo_lattes_link':fields.char('Link do Currículo Lattes', size=120),
        #'login': fields.related('user_id', 'login', type='char', string='Login', readonly=0),
        #'password': fields.related('user_id', 'password', type='char', string='Senha', readonly=0),
        #'country_id': fields.many2one('res.country', 'Nacionalidad:'),
        u'image': fields.binary(u"Foto",
            help=u"This field holds the image used as photo for the employee, limited to 1024x1024px."),
        u'birthday': fields.date(u"Data de Nascimento", required=False),
    u'polo_id':fields.many2one('ud.polo', u"Polo"),
        u'image_medium': fields.function(_get_image, fnct_inv=_set_image,
            string=u"Smal-sized photo", type="binary", multi="_get_image",
            store = {
                u'ud.employee': (lambda self, cr, uid, ids, c={}: ids, ['image'], 10),
            }),
        u'image_small': fields.function(_get_image, fnct_inv=_set_image,
            string=u"Smal-sized photo", type="binary", multi="_get_image",
            store = {
                u'hr.employee': (lambda self, cr, uid, ids, c={}: ids, ['image'], 10),
            },
            help=u"Small-sized photo of the employee. It is automatically "\
                 u"resized as a 64x64px image, with aspect ratio preserved. "\
                 u"Use this field anywhere a small image is required."),
        u'gender': fields.selection([('masculino', u'Masculino'),('feminino', u'Feminino')], u'Gênero', required=False),
        u'marital': fields.selection([('solteiro', u'Solteiro'), ('casado', u'Casado'), ('viuvo', u'Viúvo'), ('divorciado', u'Divorciado')], u'Estado Civil',required=False),
        #'department_id':fields.many2one('hr.department', 'Departamento'),
        #'address_id': fields.many2one('res.partner', 'Endereço comercial'),
       # 'address_home_id': fields.many2one('res.partner', 'Endereço'),
        #'partner_id': fields.related('address_home_id', 'partner_id', type='many2one', relation='res.partner', readonly=True, help="Partner that is related to the current employee. Accounting transaction will be written on this partner belongs to employee."),
        u'work_phone': fields.char(u'Telefone Fixo', size=32),
        u'mobile_phone': fields.char(u'Celular', size=32, required=False),
        u'work_email': fields.char(u'E-mail', size=240, required=False),
        u'notes': fields.text(u'Notas'),
        #'parent_id': fields.many2one('ud.employee', 'Gerenciador'),
        #'child_ids': fields.one2many('ud.employee', 'parent_id', 'Subordinates'),
        u'photo': fields.binary(u'Foto'),        
        # Adicionados por mim
        u'cpf':fields.char(u'CPF', size=14, help=u"Entre o CPF no formato: XXX.XXX.XXX-XX"),
        u'rg':fields.char(u'RG', size=20, required=False),
        u'orgaoexpedidor':fields.char(u'Orgão Expedidor', size=8, help=u"Sigla: Ex. SSP/SP", required=False),
        u'papel_ids': fields.one2many('ud.perfil', 'ud_papel_id', u'Papel', ondelete='cascade'),
        u'papel_setor':fields.related('papel_ids', 'tipo', store=True, type="char"),
        u'matricula':fields.related('papel_ids', 'matricula', store=True, type="char"),
        u'login_user':fields.related('user_id', 'login', store=True, type="char"),
        u'usuario_id':fields.related('user_id', 'id', store=True, type="integer"),
        u'dados': fields.one2many('ud.dados.bancarios', 'ud_conta_id', u'Dados Bancários'),
        u'nacionalidade': fields.selection((('al',u'Alemã'), ('es',u'Espanhola'), ('fr',u'Francesa'),('gr',u'Grega'),('hu',u'Húngaro'),('ir', u'Irlandesa'), ('it',u'Italiana'), ('ho',u'Holandesa'), ('pt',u'Portuguesa'), ('in',u'Inglesa'), ('rs', u'Russa'), ('ar',u'Argentina'), ('br', u'Brasileira'), ('ch',u'Chilena'), ('eu', u'Norte-Americana'), ('mx', u'Mexicana'),('chi', u'Chinesa'),('jp', u'Japonesa'),('sf',u'Sul-Africana'),('as',u'Australiana')),u'Nacionalidade',required=False),
        u'rua': fields.char(u'Rua', size=120, required=False),
        u'bairro': fields.char(u'Bairro', size=32, required=False),
        u'cidade': fields.char(u'Cidade', size=120, required=False),
        u'estado': fields.selection([('ac', u'AC'), ('al', u'AL'), ('ap', u'AP'), ('am', u'AM'), ('ba',u'BA'), ('ce',u'CE'), ('df',u'DF'), ('es',u'ES'), ('go',u'GO'), ('ma',u'MA') , ('mg',u'MG'), ('ms',u'MS'), ('mt',u'MT'), ('pa',u'PA'), ('pe',u'PE'), ('pi',u'PI'), ('pr',u'PR'), ('rj',u'RJ'), ('rn',u'RN'), ('ro',u'RO'), ('rr',u'RR'), ('rs',u'RS'), ('sc',u'SC'), ('se',u'SE'), ('sp',u'SP'), ('to', u'TO')], u'Estado', required=True),
    }
        
    def unlink(self, cr, uid, ids, context=None):
        '''
        Remove o usuário da pessoa excluida.
        '''
        res_users_ids = []
        for employee in self.browse(cr, uid, ids, context=context):
            res_users_ids.append(employee.user_id.id)
        print res_users_ids
        
        print "\n\n\n\n\n"
        if res_users_ids[0] == False or res_users_ids[0] == ID_CONTA_ADMIN:
            return super(ud_employee, self).unlink(cr, uid, ids, context=context)
        else:
            return self.pool.get('res.users').unlink(cr, uid, res_users_ids, context=context)
    
    
    def _get_default_image(self, cr, uid, context=None):
        '''
        Retorna a imagem padrão.
        '''
        image_path = addons.get_module_resource('hr', 'static/src/img', 'default_image.png')
        return tools.image_resize_image_big(open(image_path, 'rb').read().encode('base64'))
    
    

    def _valida_cpf(self, cr, uid, ids, context=None):
        '''
         Valida o CPF.
        '''
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
            if type(re.match("(?:^|\s)[-a-z0-9_.]+@(?:[-a-z0-9]+\.)+[a-z]{2,6}(?:\s|$)",str(data.work_email))) != NoneType:
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

    
    
    def _obrigar_papel(self, cr, uid, ids, context=None):
        '''
            Obriga a pessoa ter pelo menos um polo ou curso no cadastro.
        '''
        obj_papel = self.pool.get('ud.employee').browse(cr, uid, ids, context=context)       
        for data in obj_papel:
            if not data.papel_ids:
                return False
        return True
            
    
   
    
    _constraints = [
        #(_obrigar_papel, 'Pessoa precisa ter pelo menos um papel!', [u'Papéis']),
        #(_valida_cpf, u"CPF inválido!", ["\nCPF"]),
        (_valida_email, u"E-mail inválido!", ["E-mail"]),

        
        
        
    ]
    
    _defaults = {
        'image':_get_default_image,
        'marital': 'solteiro',
        'nacionalidade': 'br'
    }
    

    
    _sql_constraints = [('ud_cpf_uniq', 'unique(cpf)',u'Já existe CPF com esse número cadastrado.'),('ud_rg_uniq','unique(rg)',u'Já existe RG com esse número cadastrado.')]

ud_employee()

