# coding: utf-8
from __future__ import unicode_literals
import re
from openerp import SUPERUSER_ID
from openerp.modules.module import get_module_resource
from openerp.osv import osv, fields
import openerp.tools as tools

from usuario.usuario import ConfiguracaoUsuarioUD

# Tupla que guarda a lista dos principais bancos.
_BANCOS = [
    ('218', u'218 - Banco Bonsucesso S.A.'), ('036', u'036 - Banco Bradesco BBI S.A'),
    ('204', u'204 - Banco Bradesco Cartões S.A.'), ('237', u'237 - Banco Bradesco S.A.'),
    ('263', u'263 - Banco Cacique S.A.'), ('745', u'745 - Banco Citibank S.A.'),
    ('229', u'229 - Banco Cruzeiro do Sul S.A.'), ('001', u'001 - Banco do Brasil S.A.'),
    ('047', u'047 - Banco do Estado de Sergipe S.A.'), ('037', u'037 - Banco do Estado do Pará S.A.'),
    ('041', u'041 - Banco do Estado do Rio Grande do Sul S.A.'), ('004', u'004 - Banco do Nordeste do Brasil S.A.'),
    ('184', u'184 - Banco Itaú BBA S.A.'), ('479', u'479 - Banco ItaúBank S.A'),
    ('479A', u'479A - Banco Itaucard S.A.'), ('M09', u'M09 - Banco Itaucred Financiamentos S.A.'),
    ('389', u'389 - Banco Mercantil do Brasil S.A.'), ('623', u'623 - Banco Panamericano S.A.'),
    ('633', u'633 - Banco Rendimento S.A.'), ('453', u'453 - Banco Rural S.A.'),
    ('422', u'422 - Banco Safra S.A.'), ('033', u'033 - Banco Santander (Brasil) S.A.'),
    ('073', u'073 - BB Banco Popular do Brasil S.A.'), ('104', u'104 - Caixa Econômica Federal'),
    ('477', u'477 - Citibank N.A.'), ('399', u'399 - HSBC Bank Brasil S.A. – Banco Múltiplo'),
    ('652', u'652 - Itaú Unibanco Holding S.A.'), ('341', u'341 - Itaú Unibanco S.A.'),
    ('409', u'409 - UNIBANCO – União de Bancos Brasileiros S.A.'),
]


class Banco(osv.osv):
    """
    Classe que representa a entidade Banco.
    """
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
        ('banco_uniq', 'unique (banco)', u"Não é permitido duplicar bancos!"),
    ]

    _rec_name = "banco"

    def name_get(self, cr, uid, ids, context=None):
        """
        :see: osv.osv.name_get
        """
        bancos = dict(_BANCOS)
        return [
            (banco["id"], bancos[banco["banco"]])
            for banco in self.read(cr, uid, ids, ["banco"], context=context, load="_classic_write")
            ]

    def name_search(self, cr, uid, name='', args=None, operator='ilike', context=None, limit=100):
        """
        :see: osv.osv.name_search
        """
        bancos = dict(_BANCOS)
        res = []
        name = name.lower() if isinstance(name, (str, unicode)) else ""
        for banco in bancos:
            if name in bancos[banco].lower():
                res.append(banco)
        ids = self.search(cr, uid, [("banco", "in", res)], limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)


class DadosBancarios(osv.osv):
    """
    Classe que representa a entidade Dados Bancários.
    """
    _name = "ud.dados.bancarios"
    _description = u"Dados bancários"

    _columns = {
        "banco_id": fields.many2one("ud.banco", u"Banco", required=True, ondelete="restrict"),
        "agencia": fields.char(u"Agência", size=4, help=u"Número da Agência"),
        "dv_agencia": fields.char(u"DV Agência", size=2, help=u"Dígito verificador da Agência"),
        "conta": fields.char(u"Conta", size=10, help=u"Número da Conta"),
        "dv_conta": fields.char(u"DV Conta", size=1, help=u"Dígito verificador da Conta"),
        "operacao": fields.char(u"Operação", size=3, help=u"Tipo de conta"),
        "ud_conta_id": fields.many2one("ud.employee", u"Proprietário", invisible=True, ondelete="cascade"),

        "agencia_v": fields.related("banco_id", "agencia", type="boolean", invisible=True, readonly=True),
        "dv_agencia_v": fields.related("banco_id", "dv_agencia", type="boolean", invisible=True, readonly=True),
        "conta_v": fields.related("banco_id", "conta", type="boolean", invisible=True, readonly=True),
        "dv_conta_v": fields.related("banco_id", "dv_conta", type="boolean", invisible=True, readonly=True),
        "operacao_v": fields.related("banco_id", "operacao", type="boolean", invisible=True, readonly=True),
    }

    _rec_name = "banco_id"
    
    _constraints = [
        (lambda self, *args, **kwargs: self.valida_dados(*args, **kwargs),
         u"Já existe um registro com essas informações!", [u"Dados Bancários"]),
    ]

    def name_get(self, cr, uid, ids, context=None):
        """
        :see: osv.osv.name_get
        """
        bancos = dict(_BANCOS)
        return [(banco.id, bancos.get(banco.banco_id.banco)) for banco in self.browse(cr, uid, ids, context=context)]

    def name_search(self, cr, uid, name='', args=None, operator='ilike', context=None, limit=100):
        """
        :see: osv.osv.name_search
        """
        bancos = dict(_BANCOS)
        res = []
        name = name.lower() if isinstance(name, (str, unicode)) else ""
        for banco in bancos:
            if name in bancos[banco].lower():
                res.append(banco)
        ids = self.pool.get("ud.banco").search(cr, uid, [("banco", "in", res)], context=context)
        ids = self.search(cr, uid, [("id", "in", ids)], limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)

    def valida_dados(self, cr, uid, ids, context=None):
        for dados in self.browse(cr, uid, ids, context):
            args = [("banco_id", "=", dados.banco_id.id), ("id", "!=", dados.id)]
            if dados.agencia_v:
                args.append(("agencia", "=", dados.agencia))
            if dados.dv_agencia_v:
                args.append(("dv_agencia", "=", dados.dv_agencia))
            if dados.conta_v:
                args.append(("conta", "=", dados.conta))
            if dados.dv_conta_v:
                args.append(("dv_conta", "=", dados.dv_conta))
            if dados.operacao_v:
                args.append(("operacao", "=", dados.operacao))
            if self.search(cr, uid, args, context=context):
                return False
        return True
    
    def onchange_banco(self, cr, uid, ids, banco_id, context=None):
        """
        Ao atualizar o banco do registro atual, ele irá atualizar uns campos funcionais instantaneamente para mostrar
        somente os campos necessários de acordo com as configurações de cada banco.
        """
        if banco_id:
            banco = self.pool.get("ud.banco").read(
                cr, uid, banco_id, ["agencia", "dv_agencia", "conta", "dv_conta", "operacao"],
                context=context, load="_classic_write")
            vals = {"agencia": False, "dv_agencia": False, "conta": False, "dv_conta": False, "operacao": False}
            vals.update({"%s_v" % dado: banco.get(dado) for dado in banco.keys()})
            return {"value": vals}
        return {"value": {"agencia_v": False, "dv_agencia_v": False, "conta_v": False, "dv_conta_v": False,
                          "operacao_v": False, "agencia": False, "dv_agencia": False, "conta": False, "dv_conta": False,
                          "operacao": False}}


class Campus(osv.osv):
    """
    Classe que representa os campos do formulário Campus.
    """
    _name = 'ud.campus'
    _description = "Campus"

    _columns = {
        'name': fields.char(u'Nome', size=40, required=True, help=u"Ex.: Arapiraca, Sertão, Litoral etc."),
        'description': fields.text(u'Descrição'),

        # FIXME: Verificar os atributos "ondelete" de cada relação para verificar se era pra existir uma depência tão forte.
        'diretor': fields.many2one(u'ud.employee', u'Diretor', ondelete='cascade'),
        'diretor_acad': fields.many2one(u'ud.employee', u'Diretor Acadêmico', ondelete='cascade'),

        'is_active': fields.boolean(u'Ativo?'),
    }


class Espaco(osv.osv):
    """
    Classe que representa a entidade Espaço.
    """
    _name = 'ud.espaco'

    _columns = {
        'name': fields.char(u'Nome', size=80, required=True),
        'capacidade': fields.integer(u'Capacidade', required=True, help=u"Número de pessoas."),
        # depois trocar para inteiro
        'permite_reserva': fields.boolean(u'Permitir Reserva'),
        'campus_id': fields.many2one('ud.campus', 'Campus', required=True),
        'local_polo': fields.many2one('ud.polo', u'Polo', required=True, ondelete='cascade'),
        'local_bloco_polo': fields.many2one('ud.bloco', u'Bloco', required=True, ondelete='cascade',
                                            domain="[('ud_bloco_ids','=',local_polo)]"),
        'informacoes_adicionais': fields.text(u'Descrição'),
        'responsavel_ids': fields.many2many('ud.employee', 'ud_espaco_responsavel', 'eid', 'pid', 'Responsável')
    }

    def limpa_bloco(self, cr, uid, ids):
        """
        Limpa o campo bloco se o polo não pertencer a ele.
        """
        campos = ["local_bloco_polo"]
        valores = {}
        for campo in campos:
            valores[campo] = ""
        return {'value': valores}


class Polo(osv.osv):
    """
    Classe que representa os campos do formulário Pólo.
    """
    _name = 'ud.polo'
    _description = u"Polo"

    _columns = {
        'name': fields.char(u'Nome', size=80, required=True, help=u"Ex.: Viçosa, Penedo, Palmeira etc."),
        'campus_id': fields.many2one('ud.campus', u'Campus', required=True),
        # 'is_sede': fields.boolean('Sede?'),
        'localizacao': fields.char(u'Endereço', size=120),
        'is_active': fields.boolean(u'Ativo?'),
        'descricao': fields.text(u'Descrição'),
        'bloco_ids': fields.one2many('ud.bloco', 'ud_bloco_ids', u'Bloco'),
    }


class Bloco(osv.osv):
    """
    Classe que representa os campos do formulário Bloco.
    """
    _name = 'ud.bloco'
    _description = u'Bloco'

    _columns = {
        'name': fields.char(u'Bloco', size=80, required=True),
        'ud_bloco_ids': fields.many2one('ud.polo', u'Polo', ondelete='cascade', invisible=True),
    }

    _order = "name"


class Projeto(osv.osv):
    """
    Classe que representa os campos do formulário Projeto.
    """
    _name = "ud.projeto"
    _description = u'Projeto'

    _columns = {
        'name': fields.char(u'Nome', size=40, required=True),
        'curso_id': fields.many2one('ud.curso', u'Curso', ondelete='cascade', invisible=True),
        'data_inicio': fields.date(u'Data de inicio'),
        'data_fim': fields.date(u'Data Final (Prevista)'),
        'detalhes': fields.text(u'Descrição'),

        # Há uma maneira mais adequada de se fazer essa referência usando "inherit" evitando a adição desse campo no núcleo.
        # 'bolsistas': fields.many2one('ud.employee.nae', string='Bolsistas'), # ATENÇÃO: REFERENCIA CRUZADA: Quando for implantar no servidor, será necessário comentar essa linha. Após as tabelas terem sido criadas, descomentar.
    }


class Setor(osv.osv):
    """
    Classe que representa os campos do formulário Setor.
    """
    _name = 'ud.setor'
    _description = u'Setor'

    _columns = {
        'name': fields.char(u'Nome', size=80, required=True),
        'descricao': fields.text(u'Descrição'),
        'polo_id': fields.many2one('ud.polo', u'Polo', required=True, ondelete='cascade'),
        'sigla': fields.char(u'Sigla', size=50, required=True),
        'is_active': fields.boolean(u'Ativo?'),
    }


class Curso(osv.osv):
    """
    Classe que representa os campos do formulário Curso.
    """
    _name = 'ud.curso'
    _description = u'Curso'

    _columns = {
        'name': fields.char(u'Nome', size=40, help=u"Ex.: Ciência da Computação", required=True),
        'polo_id': fields.many2one('ud.polo', u'Polo', ondelete='cascade', required=True),
        'coordenador': fields.many2one('ud.employee', u'Coordenador', ondelete='cascade'),
        'is_active': fields.boolean(u'Ativo?'),
        'description': fields.text(u'Descrição'),
        'disciplina_ids': fields.one2many('ud.disciplina', 'ud_disc_id', u'Disciplina'),
        'projeto_ids': fields.one2many('ud.projeto', 'curso_id', u'Projetos'),
    }


class Disciplina(osv.osv):
    """
    Classe que representa os campos do formulário Disciplina (Associada com a classe Curso).
    """
    _name = 'ud.disciplina'
    _description = u'Disciplina'

    _columns = {
        'codigo': fields.char(u'Código', size=15, required=True),
        'name': fields.char(u'Nome', size=40, required=True),
        'ch': fields.integer(u'Carga Horária', size=10, required=True),
        'descricao': fields.text(u'Descrição'),
        'ud_disc_id': fields.many2one('ud.curso', u'Curso', ondelete='cascade', invisible=True),
    }

    _constraints = [
        (lambda cls, *args, **kwargs: cls.valida_ch(*args, **kwargs),
         u"Carga horária não possui um número válido", [u"Carga Horária"]),
    ]

    def valida_ch(self, cr, uid, ids, context=None):
        for disc in self.browse(cr, uid, ids, context):
            if disc.ch < 1:
                return False
        return True


class Perfil(osv.osv):  # Classe papel
    """
    Classe que representa os campos do formulário Papéis (Associada a classe ud_employee).
    """
    _name = 'ud.perfil'
    _description = 'Papel'

    _TIPOS_PERFIL = [('p', u'Docente'), ('t', u'Técnico'), ('a', u'Discente'), ('x', u'Terceirizado'), ('o', u'Outra')]
    _TIPOS_BOLSA = [('per', u'Permanência'), ('pai', u'Painter'), ('pibic', u'PIBIC-CNPq'), ('pibip', u'PIBIB-Ação'),
                     ('pibit', u'PIBIT-CNPq'), ('aux', u'Auxílio Alimentação'), ('aux_t', u'Auxílio Transporte'),
                     ('bdi', u'BDI'), ('bdai', u'BDAI'), ('pibid', u'PIBID'), ('m', u'Monitoria')]
    _TIPOS_DOCENTE = [('pa', u'Professor Assistente'), ('pad', u'Professor Adjunto'), ('pt', u'Professor Titular')]

    _columns = {
        'tipo': fields.selection(_TIPOS_PERFIL, u'Tipo'),
        'is_bolsista': fields.boolean(u'Bolsista'),
        'tipo_bolsa': fields.selection(_TIPOS_BOLSA, u'Tipo de Bolsa'),
        'valor_bolsa': fields.char(u"Valor da Bolsa (R$)", size=7), # FIXME: Esse campo poderia ser "float"
        'tipo_docente': fields.selection(_TIPOS_DOCENTE, u'Tipo de Docente'),
        'matricula': fields.char(u'Matricula', size=15, help=u"Ex.: 123456789", required=True),
        'data_validade': fields.date(u'Data de Validade'),
        'ud_papel_id': fields.many2one('ud.employee', u'Papel', ondelete='cascade', invisible=True),
        'ud_cursos': fields.many2one('ud.curso', u'Curso', ondelte='cascade'),
        'ud_setores': fields.many2one('ud.setor', u'Setor'),
        'ud_projetos': fields.many2one('ud.projeto', u'Setor')
    }

    _rec_name = "matricula"

    _sql_constraints = [
        ('papel_uniq', 'unique (matricula,tipo)', u'Matricula já cadastrada para esse tipo de papel.'),
    ]

    _constraints = [
        (lambda self, *args, **kwargs: self._setor_ou_curso(*args, **kwargs), u'Preencha pelo menos um dos campos.',
         ['Setor', 'Curso'])
    ]

    def _setor_ou_curso(self, cr, uid, ids, context=None):
        """
        Método que valida a entrada de Setor ou Curso (sem deixá-los em branco).

        :return: False se os campos estão em branco ou True, caso contrário.
        """
        obj_setor_curso = self.pool.get('ud.perfil').browse(cr, uid, ids, context=context)
        for data in obj_setor_curso:
            if not data.ud_setores and not data.ud_cursos:
                return False
        return True


class Employee(osv.osv):
    """
    Classe que representa os campos do formulário Pessoa.
    """
    _name = "ud.employee"
    _description = u"Employee"
    _inherits = {'resource.resource': 'resource_id'}

    def _get_image(self, cr, uid, ids, name, args, context=None):
        """
         Retorna a imagem redimensionada.
        """
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            result[obj.id] = tools.image_get_resized_images(obj.image)
        return result

    def _set_image(self, cr, uid, id, name, value, args, context=None):
        """
         Seta a imagem.
        """
        return self.write(cr, uid, [id], {'image': tools.image_resize_image_big(value)}, context=context)

    _NACIONALIDADES = [
        ('al', u'Alemã'), ('es', u'Espanhola'), ('fr', u'Francesa'), ('gr', u'Grega'), ('hu', u'Húngaro'),
        ('ir', u'Irlandesa'), ('it', u'Italiana'), ('ho', u'Holandesa'), ('pt', u'Portuguesa'), ('in', u'Inglesa'),
        ('rs', u'Russa'), ('ar', u'Argentina'), ('br', u'Brasileira'), ('ch', u'Chilena'), ('eu', u'Norte-Americana'),
        ('mx', u'Mexicana'), ('chi', u'Chinesa'), ('jp', u'Japonesa'), ('sf', u'Sul-Africana'), ('as', u'Australiana')
    ]

    _ESTADOS = [
        ('ac', u'AC'), ('al', u'AL'), ('ap', u'AP'), ('am', u'AM'), ('ba', u'BA'), ('ce', u'CE'), ('df', u'DF'),
        ('es', u'ES'), ('go', u'GO'), ('ma', u'MA'), ('mg', u'MG'), ('ms', u'MS'), ('mt', u'MT'), ('pa', u'PA'),
        ('pe', u'PE'), ('pi', u'PI'), ('pr', u'PR'), ('rj', u'RJ'), ('rn', u'RN'), ('ro', u'RO'), ('rr', u'RR'),
        ('rs', u'RS'), ('sc', u'SC'), ('se', u'SE'), ('sp', u'SP'), ('to', u'TO')
    ]

    _columns = {
        'curriculo_lattes_link': fields.char('Link do Currículo Lattes', size=120),
        'image': fields.binary(u"Foto",
                               help=u"This field holds the image used as photo for the employee, limited to 1024x1024px."),
        'birthday': fields.date(u"Data de Nascimento"),
        'polo_id': fields.many2one('ud.polo', u"Polo"),
        'image_medium': fields.function(_get_image, fnct_inv=_set_image, string=u"Smal-sized photo", type="binary",
                                        multi="_get_image",
                                        store={'ud.employee': (lambda self, cr, uid, ids, c=None: ids, ['image'], 10)}),
        'image_small': fields.function(_get_image, fnct_inv=_set_image, string=u"Smal-sized photo", type="binary",
                                       multi="_get_image",
                                       store={'hr.employee': (lambda self, cr, uid, ids, c=None: ids, ['image'], 10)},
                                       help=(u"Small-sized photo of the employee. It is automatically "
                                             u"resized as a 64x64px image, with aspect ratio preserved. "
                                             u"Use this field anywhere a small image is required.")),
        'gender': fields.selection([('masculino', u'Masculino'), ('feminino', u'Feminino')], u'Gênero'),
        'marital': fields.selection(
            [('solteiro', u'Solteiro'), ('casado', u'Casado'), ('viuvo', u'Viúvo'), ('divorciado', u'Divorciado')],
            u'Estado Civil'
        ),
        'work_phone': fields.char(u'Telefone Fixo', size=32),
        'mobile_phone': fields.char(u'Celular', size=32),
        'work_email': fields.char(u'E-mail', size=240),
        'notes': fields.text(u'Notas'),
        'photo': fields.binary(u'Foto'),
        # Adicionados por mim
        'cpf': fields.char(u'CPF', size=14, help=u"Entre o CPF no formato: XXX.XXX.XXX-XX"),
        'rg': fields.char(u'RG', size=20),
        'orgaoexpedidor': fields.char(u'Orgão Expedidor', size=8, help=u"Sigla: Ex. SSP/SP"),
        'papel_ids': fields.one2many('ud.perfil', 'ud_papel_id', u'Papel'),
        'papel_setor': fields.related('papel_ids', 'tipo', store=True, type="char"),
        'matricula': fields.related('papel_ids', 'matricula', store=True, type="char"),
        'dados': fields.one2many('ud.dados.bancarios', 'ud_conta_id', u'Dados Bancários'),
        'nacionalidade': fields.selection(_NACIONALIDADES, u'Nacionalidade'),
        'rua': fields.char(u'Rua', size=120),
        "numero": fields.char(u"Número", size=8),
        'bairro': fields.char(u'Bairro', size=32),
        'cidade': fields.char(u'Cidade', size=120),
        'estado': fields.selection(_ESTADOS, u'Estado'),
        'resource_id': fields.many2one('resource.resource', ondelete='set null')
    }

    _constraints = [
        # (lambda self, *args, **kwargs: self._obrigar_papel(*args, **kwargs), 'Pessoa precisa ter pelo menos um papel!', [u'Papéis']),
        (lambda self, *args, **kwargs: self._valida_cpf(*args, **kwargs), u"CPF inválido! Verifique se está correto. Ex.: 111.111.111-00", ["\nCPF"]),
        (lambda self, *args, **kwargs: self._valida_email(*args, **kwargs),
         u"E-mail inválido! Verifique se está correto e se não há espaços", ["E-mail"]),
    ]

    _defaults = {
        'image': lambda self, *args, **kwargs: self._get_default_image(*args, **kwargs),
        'marital': 'solteiro',
        'nacionalidade': 'br'
    }

    _sql_constraints = [
        ("ud_cpf_uniq", "unique(cpf)", u'Já existe CPF com esse número cadastrado.'),
        ("ud_rg_uniq", "unique(rg)", u'Já existe RG com esse número cadastrado.'),
    ]

    def name_get(self, cr, uid, ids, context=None):
        context = context or {}
        return [
            (pessoa.id, pessoa.name + context.get("complemento", {}).get(pessoa.id, ""))
            for pessoa in self.browse(cr, uid, ids, context)
        ]

    def name_search(self, cr, uid, name='', args=None, operator='ilike', context=None, limit=100):
        context = context or {}
        context["complemento"] = {}
        ids = []
        perfil_model = self.pool.get("ud.perfil")
        for perfil in perfil_model.search(cr, uid, [("matricula", "=", name)]):
            pessoa_id = perfil_model.browse(cr, uid, perfil, context).ud_papel_id.id
            context["complemento"][pessoa_id] = u" (Matrícula/SIAPE: %s)" % name
            ids.append(pessoa_id)
        res = set(super(Employee, self).name_search(cr, uid, name, args, operator, context, limit))
        if ids:
            res = res.union(self.name_get(cr, uid, ids, context))
        if limit:
            return list(res)[:limit]
        return list(res)

    def create(self, cr, uid, vals, context=None):
        res = super(Employee, self).create(cr, uid, vals, context)
        self.criar_usuarios(cr, uid, res, context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        super(Employee, self).write(cr, uid, ids, vals, context)
        self.criar_usuarios(cr, uid, ids, context)
        return True

    def unlink(self, cr, uid, ids, context=None):
        if ConfiguracaoUsuarioUD.get_exclusao_unica(self, cr, uid, context):
            usuarios = [
                pessoa.user_id.id for pessoa in self.browse(cr, uid, ids, context) if pessoa.user_id.id != SUPERUSER_ID
            ]
            self.pool.get('res.users').unlink(cr, uid, usuarios, context=context)
        return super(Employee, self).unlink(cr, uid, ids, context=context)

    def criar_usuarios(self, cr, uid, ids, context):
        if isinstance(ids, (int, long)):
            ids = [ids]
        user_model = self.pool.get("res.users")
        for pessoa in self.browse(cr, uid, ids, context):
            if not pessoa.user_id and pessoa.cpf:
                login = pessoa.cpf.replace(".", "").replace("-", "")
                usuario = user_model.search(cr, SUPERUSER_ID, [("login", "=", login)], context)
                if usuario:
                    if self.search(cr, uid, [("user_id", "=", usuario[0])], context=context):
                        raise osv.except_osv(u"Multiplos vínculos", u"Há outra pessoa vinculada a esse login: '%s'." % login)
                    usuario = usuario[0]
                else:
                    dados = {
                        "name": pessoa.name, "tz": "America/Maceio",
                        "login": login,
                        "new_password": pessoa.cpf.replace(".", "").replace("-", "")[:6]
                    }
                    usuario = user_model.create(cr, SUPERUSER_ID, dados, context)
                pessoa.write({"user_id": usuario})
        return True

    def _get_default_image(self, cr, uid, context=None):
        """
        Retorna a imagem padrão.
        """
        # image_path = addons.get_module_resource('hr', 'static/src/img', 'default_image.png')
        image_path = get_module_resource('hr', 'static/src/img', 'default_image.png')
        return tools.image_resize_image_big(open(image_path, 'rb').read().encode('base64'))

    def _valida_cpf(self, cr, uid, ids, context=None):
        """
         Valida o CPF.
        """

        def calcula_dv(cpf, pos_dv=-2):
            dv = 0
            for i in range(len(cpf[:pos_dv])):
                dv += int(cpf[i]) * (11 - (i + (-(pos_dv + 1))))
            dv %= 11
            return 0 if dv < 2 else 11 - dv
        padrao = re.compile("^\d{3}\.\d{3}\.\d{3}-\d{2}$")
        for pessoa in self.browse(cr, uid, ids, context=context):
            cpf = pessoa.cpf
            if cpf:
                if not padrao.match(cpf):
                    return False
                if cpf.count(cpf[0]) == 11:
                    return False
                cpf = cpf.replace(".", "").replace("-", "")
                if int(cpf[-2]) != calcula_dv(cpf) or int(cpf[-1]) != calcula_dv(cpf, -1):
                    return False
        return True

    def _valida_email(self, cr, uid, ids, context=None):
        """
        Método que valida os campos do formulário Pessoa. Ex.: RG:111111 (sem traços).
        return: False se dados passados estão fora desse padrão ou True, caso contrário.
        """
        padrao_email = re.compile("^[a-zA-Z]+(?:[.\w+]*)@[a-zA-Z]+(?:\.[a-zA-Z]+)+$")
        for data in self.browse(cr, uid, ids, context=context):
            if data.work_email and not padrao_email.match(data.work_email):
                return False
        return True

    def _obrigar_papel(self, cr, uid, ids, context=None):
        """
        Obriga a pessoa ter pelo menos um polo ou curso no cadastro.
        """
        for data in self.pool.get('ud.employee').browse(cr, uid, ids, context=context):
            if not data.papel_ids:
                return False
        return True
