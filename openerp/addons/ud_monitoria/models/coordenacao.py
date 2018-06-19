# coding: utf-8
from datetime import datetime, timedelta
from re import compile

from openerp import SUPERUSER_ID
from openerp.osv import fields, osv
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from util import get_ud_pessoa_id, data_hoje


class Semestre(osv.Model):
    _name = "ud_monitoria.semestre"
    _description = u"Configurações definidas para um semestre (UD)"
    _order = "is_active desc, semestre desc"
    _rec_name = "semestre"

    # Métodos para campos calculados
    def get_dados_bolsas(self, cr, uid, ids, campo, args, context=None):
        """
        Calcula o total de bolsas distribuídas entre os cursos e bolsas utilizadas.

        :return: {ID_SEMESTRE: {'bolsas_distribuidas': QTD_BOLSAS_DIST, 'bolsas_disponiveis': QTD_BOLSAS_DISP}}
        """
        res = {}
        for semestre in self.browse(cr, uid, ids, context):
            res[semestre.id] = {'bolsas_distribuidas': 0, 'bolsas_disponiveis': semestre.max_bolsas}
            for bc in semestre.bolsas_curso_ids:
                res[semestre.id]['bolsas_distribuidas'] += bc.bolsas
                res[semestre.id]['bolsas_disponiveis'] -= bc.utilizadas
            res[semestre.id]['bolsas_n_distribuidas'] = semestre.max_bolsas - res[semestre.id]['bolsas_distribuidas']
        return res

    def update_bolsas_curso(self, cr, uid, ids, context=None):
        """
        Busca os ids dos semestres que serão atualizados baseado nos ids informados de BolsasCurso.

        :return: [IDS_SEMESTRE]
        """
        sql = '''
        SELECT sm.id FROM %(t_sm)s sm INNER JOIN %(t_bc)s bc ON (sm.id = bc.semestre_id) WHERE bc.id in (%(ids)s);
        ''' % {
            't_sm': self.pool.get('ud_monitoria.semestre')._table,
            't_bc': self.pool.get('ud_monitoria.bolsas_curso')._table,
            'ids': str(ids).lstrip('[(').rstrip(']),').replace('L', '')
        }
        cr.execute(sql)
        res = cr.fetchall()
        if res:
            return [linha[0] for linha in res]
        return []

    def get_bolsas_disponiveis(self, cr, uid, ids, campo, args, context=None):
        """
        Calcula o total de bolsas sem utilização
        """
        res = {}
        for semestre in self.browse(cr, uid, ids, context):
            res[semestre.id] = 0
            for dist in semestre.bolsas_curso_ids:
                res[semestre.id] += dist.bolsas_disponiveis
        return res

    _columns = {
        "id": fields.integer(u"ID", readonly=True, invisible=True),
        "semestre": fields.char(u"Semestre", size=6, required=True, help=u"Semestre no formato '2016.1'"),
        "max_bolsas": fields.integer(u"Máximo de Bolsas", required=True, help=u"Número máximo de bolsas disponíveis para o semestre"),
        "bolsas_distribuidas": fields.function(get_dados_bolsas, type="integer", string=u"Bolsas Distribuidas",
                                               multi=True, help=u"Bolsas distribuidas entre os cursos"),
        "bolsas_n_distribuidas": fields.function(get_dados_bolsas, type="integer", string=u"Bolsas não Distribuidas",
                                                 multi=True, help=u"Bolsas não distribuidas entre os cursos"),
        "bolsas_disponiveis": fields.function(get_dados_bolsas, type="integer", string=u"Bolsas não utilizadas",
                                              multi=True, help=u"Bolsas disponíveis para novos bolsistas"),
        "is_active": fields.boolean(u"Ativo", readonly=True),
        "data_i_frequencia": fields.date(u"Envio de Frequência", required=True, help=u"Próxima data para submissão da frequências"),
        "intervalo_frequencia": fields.integer(u"Período (Dias)", required=True, help=u"Intervalo de submissão de frequências"),
        "bolsas_curso_ids": fields.one2many("ud_monitoria.bolsas_curso", "semestre_id", u"Distribuição de Bolsas",
                                                   help=u"Permite distribuir bolsas entre cursos ativos"),
        "processos_seletivos_ids": fields.one2many("ud_monitoria.processo_seletivo", "semestre_id",
                                                   u"Processos Seletivos"),
        "ocorrencias_ids": fields.one2many("ud_monitoria.ocorrencia", "semestre_id", u"Ocorrências semestrais",
                                           help=u"Registro de ocorrências do semestre"),
    }
    _constraints = [
        (lambda cls, *args, **kwargs: cls.valida_intervalo_frequencia(*args, **kwargs),
         u"O intervalo da frequência deve ser maior que 0.", [u"Período da frequência"]),
        (lambda cls, *args, **kwargs: cls.valida_semestre(*args, **kwargs),
         u"Semestre inválido.", [u"Semestre"]),
        (lambda cls, *args, **kwargs: cls.valida_bolsas(*args, **kwargs),
         u"Número máximo de Bolsas excedido.", [u"Distribuição de Bolsas"]),
        (lambda cls, *args, **kwargs: cls.valida_valor_negativo(*args, **kwargs),
         u"Valores negativos não são permitidos.", [u"Máximo de Bolsas / Período (Dias)"]),
    ]
    _sql_constraints = [
        ("semestre_unique", "unique (semestre)", u"Não é permitido criar registros com semestres iguais!"),
    ]
    _defaults = {
        "intervalo_frequencia": 10,
        "semestre": lambda cls, *args, **kwargs: cls.semestre_disponivel(*args, **kwargs),
        "is_active": True,
        "data_i_frequencia": (datetime.utcnow() + timedelta(30)).strftime("%Y-%m-%d"),
    }

    # Métodos sobrescritos
    def copy(self, cr, uid, id, default=None, context=None):
        """
        Configuração de como um registro será duplicado.
        """
        default = default or {}
        semestre = default.get('semestre', None)
        default.update({
            'semestre': self.semestre_disponivel(cr, uid, context, semestre),
            'data_i_frequencia': (datetime.utcnow() + timedelta(30)).strftime('%Y-%m-%d'),
            'processos_seletivos_ids': [],
            'relatorio_discentes_ids': [],
            'ocorrencias_ids': [],
            'is_active': True,
            'bolsas_curso_ids': [
                (0, 0, {'curso_id': bc.curso_id.id, 'bolsas': bc.bolsas})
                for bc in self.browse(cr, uid, id).bolsas_curso_ids if bc.curso_id.is_active
            ]
        })
        if context is None:
            context = {}
        context = context.copy()
        data = self.copy_data(cr, uid, id, default, context)
        new_id = self.create(cr, uid, data, context)
        return new_id

    # Valores Padrão
    def semestre_disponivel(self, cr, uid, context=None, semestre=None):
        if not semestre:
            semestre = self.search(cr, uid, [], limit=1, order='semestre desc')
            if semestre:
                semestre = self.browse(cr, uid, semestre[0]).semestre.split('.')
                if semestre[1] == '1':
                    return '%s.2' % semestre[0]
                return '%i.1' % (int(semestre[0]) + 1)
            hoje = datetime.utcnow()
            return '%d.%d' % (hoje.year, 1 if hoje.month <= 6 else 2)

        ano, semestre = map(int, semestre.split('.'))
        while True:
            if self.search_count(cr, uid, [('semestre', '=', '%d.%d' % (ano, semestre))], context=context) > 0:
                if semestre == 1:
                    semestre = 2
                else:
                    ano += 1
                    semestre = 1
            else:
                return '%d.%d' % (ano, semestre)

    # Validadores
    def valida_intervalo_frequencia(self, cr, uid, ids, context=None):
        """
        Verifica se o internvalo de submissão de frequências dos discentes é menor que 1.
        """
        for registro in self.browse(cr, uid, ids, context=context):
            if (registro.intervalo_frequencia < 1):
                return False
        return True

    def valida_semestre(self, cr, uid, ids, context=None):
        """
        Verifica se o semestre está no padrão de ano e semestre AAAA.S.
        """
        padrao = compile("\d{4}\.[12]")
        for semestre in self.browse(cr, uid, ids, context=context):
            if not padrao.match(semestre.semestre):
                return False
        return True

    def valida_bolsas(self, cr, uid, ids, context=None):
        """
        Verifica se a soma das bolsas distribuídas entre os cursos ultrapassou a quantidade máxima para o semestre.
        """
        for semestre in self.browse(cr, uid, ids, context):
            bolsas = 0
            for dist in semestre.bolsas_curso_ids:
                bolsas += dist.bolsas
            if bolsas > semestre.max_bolsas:
                return False
        return True

    def valida_valor_negativo(self, cr, uid, ids, context=None):
        for semestre in self.browse(cr, uid, ids, context):
            if semestre.max_bolsas < 0 or semestre.intervalo_frequencia < 0:
                return False
        return True

    # Ações de Botão
    def ativar_registro(self, cr, uid, ids, context=None):
        """
        Marca o registro como ativo
        """
        return self.write(cr, uid, ids, {"is_active": True}, context=context)

    def desativar_registro(self, cr, uid, ids, context=None):
        """
        Marca o registro como inativo.
        """
        return self.write(cr, uid, ids, {"is_active": False}, context=context)

    def atualizar_status_processos_seletivos(self, cr, uid, ids, context=None):
        ps = self.pool.get('ud_monitoria.processo_seletivo')
        sql = "UPDATE " + ps._table + " SET state='%(status)s' WHERE semestre_id in (" \
              + str(ids).lstrip('[(').rstrip(']),').replace('L', '') + ") AND state NOT IN ('invalido', '%(status)s') AND %(condicao)s;"

        hoje = datetime.utcnow().strftime(DEFAULT_SERVER_DATE_FORMAT)
        cr.execute(sql % {'status': 'demanda', 'condicao': "prazo_demanda >= '%s'" % hoje})
        cr.execute(sql % {'status': 'novo', 'condicao': "prazo_demanda < '%(hj)s' AND data_inicio > '%(hj)s'" % {'hj': hoje}})
        cr.execute(sql % {'status': 'andamento', 'condicao': "data_inicio <= '%(hj)s' AND data_fim >= '%(hj)s'" % {'hj': hoje}})
        cr.execute(sql % {'status': 'encerrado', 'condicao': "data_fim < '%(hj)s'" % {'hj': hoje}})
        return True

    def inserir_cursos_inscricoes(self, cr, uid, ids, context=None):
        inscricao_model = self.pool.get('ud_monitoria.inscricao')
        inscricoes = inscricao_model.search(cr, uid, [('bolsas_curso_id', '=', False)])
        for inscricao in inscricao_model.browse(cr, uid, inscricoes):
            inscricao.write({'bolsas_curso_id': inscricao.disciplina_id.bolsas_curso_id.id})
        return True


class Ocorrencia(osv.Model):
    _name = "ud_monitoria.ocorrencia"
    _description = u"Registro geral de ocorrências do semestre (UD)"
    _order = "create_date desc"
    _columns = {
        "responsavel_id": fields.many2one("ud.employee", u"Responsável", required=True, readonly=True,
                                          ondelete="restrict", help=u"Pessoa responsável pela ocorrência"),
        "create_date": fields.datetime(u"Data da ocorrência", readonly=True),
        "name": fields.char(u"Nome", required=True),
        "envolvidos_ids": fields.many2many("ud.employee", "ud_monitoria_ocorrencia_envolvidos", "ocorrencia_id", "pessoa_id",
                                           u"Envolvidos", ondelete="restrict"),
        "descricao": fields.text(u"Descrição"),
        "semestre_id": fields.many2one("ud_monitoria.semestre", u"Semestre", required=True, ondelete="cascade"),
    }
    _defaults = {
        "responsavel_id": lambda cls, *args, **kwargs: cls.responsavel(*args, **kwargs),
    }

    def create(self, cr, uid, vals, context=None):
        """
        === Extensão do método osv.Model.create
        Impede que seja criado novos logs de ocorrências se o registro semestral correspondente estiver inativo.

        :raise osv.except_osv: Caso registro semestral esteja inativo.
        """
        semestre = vals.get("semestre_id", None)
        if semestre and not self.pool.get("ud_monitoria.semestre").browse(cr, SUPERUSER_ID, semestre).is_active:
            raise osv.except_osv(u"Registro Semestral", u"O registro do semestre em questão está inativo")
        return super(Ocorrencia, self).create(cr, uid, vals, context)

    def responsavel(self, cr, uid, context=None):
        """
        Busca o perfil no núcleo do responsável atualmente logado.
        """
        responsavel = self.pool.get("ud.employee").search(cr, SUPERUSER_ID, [("user_id", "=", uid)], limit=2)
        if not responsavel:
            raise osv.except_osv(
                u"Registro Inexistente",
                u"Não é possível realizar essa alteração enquanto seu login não estiver vinculado ao núcleo"
            )
        if len(responsavel) > 1:
            raise osv.except_osv(
                u"Multiplos vínculos",
                u"Não é possível realizar essa alteração enquanto seu login possuir multiplos vínculos no núcleo"
            )
        return responsavel[0]


class BolsasCurso(osv.Model):
    _name = "ud_monitoria.bolsas_curso"
    _description = u"Distribuição de bolsas de cursos (UD)"

    # Métodos para campos calculados
    def get_dados_bolsas(self, cr, uid, ids, campo, args, context=None):
        """
        Define o valor do número de bolsas utilizadas nos documentos dos discentes.
        """
        res = {}
        for bc in self.browse(cr, uid, ids, context):
            res[bc.id] = {'utilizadas': 0, 'disponiveis': bc.bolsas, 'distribuidas': 0}
            for disc in bc.disciplina_ids:
                res[bc.id]['distribuidas'] += disc.bolsistas
                res[bc.id]['utilizadas'] += disc.bolsas_utilizadas
                res[bc.id]['disponiveis'] -= disc.bolsas_utilizadas
        return res

    _columns = {
        'id': fields.integer("ID", readonly=True, invisible=True),
        'curso_id': fields.many2one("ud.curso", u"Curso", required=True, ondelete="restrict", domain=[("is_active", "=", True)]),
        'is_active': fields.related("curso_id", "is_active", type="boolean", string=u"Curso Ativo?", readonly=True,
                                    help=u"Identifica se atualmente o curso está ativo ou não"),
        'bolsas': fields.integer(u"Bolsas", required=True, help=u"Número de bolsas disponibilizadas para o curso"),
        'utilizadas': fields.function(get_dados_bolsas, type="integer", string=u"Bolsas utilizadas",
                                      multi='bolsas_curso', help=u"Número de bolsas com vínculo com discentes"),
        'disponiveis': fields.function(get_dados_bolsas, type="integer", string=u"Bolsas sem uso",
                                       multi='bolsas_curso', help=u"Bolsas disponíveis para novos bolsistas"),
        'distribuidas': fields.function(get_dados_bolsas, type='integer', string=u'Bolsas distribuidas',
                                        multi='bolsas_curso', help=u'Número de bolsas distribuídas entre disciplinas'),
        'disciplina_ids': fields.one2many('ud_monitoria.disciplina', 'bolsas_curso_id', u'Disciplinas'),
        'semestre_id': fields.many2one("ud_monitoria.semestre", u"Semestre", ondelete="cascade", domain=[('is_active', '=', True)]),
    }
    _constraints = [
        (lambda cls, *args, **kwargs: cls.valida_bolsas(*args, **kwargs),
         u"A quantidade de bolsas não pode ultrapassa a quatidade máxima para o semestre.", [u"Bolsas"]),
        (lambda cls, *args, **kwargs: cls.valida_bolsas_distribuidas(*args, **kwargs),
         u"A quantidade de bolsas não pode ser menor do que a quantidade de bolsas distribuídas entre suas disciplinas",
         [u"Bolsas"]),
        (lambda cls, *args, **kwargs: cls.valida_valor_negativo(*args, **kwargs),
         u"Valor negativo não é permitido.", [u"Bolsas"]),
    ]
    _sql_constraints = [
        ("curso_semestre_unique", "unique(curso_id,semestre_id)",
         u"Ofertas de cursos não podem ser duplicadas no mesmo semestre."),
    ]

    # Métodos sobrescritos
    def default_get(self, cr, uid, fields_list, context=None):
        res = super(BolsasCurso, self).default_get(cr, uid, fields_list, context)
        context = context or {}
        if context.get('active_model', None) == 'ud_monitoria.semestre' and context.get('active_id', False):
            res['semestre_id'] = context['active_id']
        return res

    def name_get(self, cr, uid, ids, context=None):
        """
        === Sobrescrita do método osv.Model.name_get
        O nome do modelo passa a ser o nome do curso.
        """
        return [(bc.id, bc.curso_id.name)
                for bc in self.browse(cr, uid, ids, context)]

    def name_search(self, cr, uid, name='', args=None, operator='ilike', context=None, limit=100):
        """
        === Sobrescrita do método osv.Model.name_search
        Pesquisa os objetos a partir do nome do curso em campos many2one.
        """
        cursos_ids = self.pool.get('ud.curso').search(cr, SUPERUSER_ID, [('name', operator, name)], context=context)
        ids = self.search(cr, SUPERUSER_ID, (args or []) + [('curso_id', 'in', cursos_ids)], limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        context = context or {}
        args2 = []
        if context.get('coordenador_monitoria_curso', False):
            args2 = [('curso_id', 'in', self.pool.get('ud.curso').search(cr, SUPERUSER_ID, [('coord_monitoria_id', '=', get_ud_pessoa_id(self, cr, uid))]))]
        if context.get('liberacao_disciplina', False):
            args2 = (args2 or []) + [('semestre_id', 'in', self.pool.get('ud_monitoria.semestre').search(cr, SUPERUSER_ID, [('is_active', '=', True)]))]
        if args2:
            args = (args or []) + args2
        return super(BolsasCurso, self).search(cr, uid, args, offset, limit, order, context, count)

    # Validador
    def valida_bolsas(self, cr, uid, ids, context=None):
        """
        Verifica se a quantidade máxima de bolsas não utrapassa a soma total de bolsas distribuída entre os cursos.

        :return: True, se não utrapassa, False, caso contrário
        """
        for bc in self.browse(cr, uid, ids, context):
            bolsas = 0
            for outras_bc in bc.semestre_id.bolsas_curso_ids:
                if outras_bc.id != bc.id:
                    bolsas += outras_bc.bolsas
            if bc.semestre_id.max_bolsas < (bolsas + bc.bolsas):
                return False
        return True

    def valida_bolsas_distribuidas(self, cr, uid, ids, context=None):
        """
        Verifica se a quantidade de bolsas não é menor que a quantidade de bolsas distribuídas entre duas disciplinas.

        :return: True, se condição atendida, False, caso contrário.
        """
        for bc in self.browse(cr, uid, ids, context):
            if bc.bolsas < bc.distribuidas:
                return False
        return True

    def valida_valor_negativo(self, cr, uid, ids, context=None):
        for bc in self.browse(cr, uid, ids, context):
            if bc.bolsas < 0:
                return False
        return True
