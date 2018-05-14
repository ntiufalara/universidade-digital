# coding: utf-8
from datetime import datetime, timedelta
from re import compile
from openerp import SUPERUSER_ID
from openerp.osv import osv, fields, orm
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.translate import _
from .util import regex_regra, regex_order, regex_espacos, regex_clausula, _MESES, data_hoje

regex_hora = compile("^[0-2][0-9]:[0-5][0-9]$")


class DocumentosDiscente(osv.Model):
    _name = 'ud_monitoria.documentos_discente'
    _description = u'Documentos de monitoria do discente (UD)'
    _order = 'is_active desc, disciplina_id, state, tutor'  # TODO: Verificar essa ordenação
    _STATES = [('reserva', u'Cadastro de Reserva'), ('n_bolsista', u'Não Bolsista'),
               ('bolsista', u'Bolsista'), ('desligado', u'Desligado(a)')]

    # Métodos para campos funcionais
    def calcula_ch(self, cr, uid, ids, campo, args, context=None):
        """
        Calcula a carga horária total que o discente atribuiu em seus horários de atendimento.
        """
        def converte(dt):
            horas = divmod(dt.seconds, 3600)
            minutos = divmod(horas[1], 60)
            return horas[0], minutos[0]

        def dif_horas(h):
            return datetime.strptime(h.hora_f, '%H:%M') - datetime.strptime(h.hora_i, '%H:%M')

        res = {}
        for doc in self.browse(cr, uid, ids, context=context):
            tempo = None
            for h in doc.horario_ids:
                tempo = tempo and tempo + dif_horas(h) or dif_horas(h)
            tempo = converte(tempo)
            # tempo = converte(sum([dif_horas(h) for h in doc.horario_ids]))
            res[doc.id] = '%s%s%s' % (
                tempo[0] and '%i hora%s' % (tempo[0], 's' if tempo[0] > 1 else '') or '',
                tempo[0] and tempo[1] and ' e ' or '',
                tempo[1] and '%i minuto%s' % (tempo[1], 's' if tempo[1] > 1 else '') or '',
            )
        return res

    def frequencia_controle(self, cr, uid, ids, campo, args, context=None):
        """
        Define se o discente pode adicionar novas frequências.
        """
        res = {}
        hoje = data_hoje(self, cr, uid)
        for doc in self.browse(cr, SUPERUSER_ID, ids, context):
            if doc.disciplina_id.is_active:
                data = datetime.strptime(doc.disciplina_id.semestre_id.data_i_frequencia, DEFAULT_SERVER_DATE_FORMAT).date()
                res[doc.id] = data <= hoje <= (data + timedelta(doc.disciplina_id.semestre_id.intervalo_frequencia))
            else:
                res[doc.id] = False
        return res

    def horas_alteradas(self, cr, uid, ids, context=None):
        """
        Define quais documentos deverão ter sua carga horária atualizada.
        """
        return tuple(set(
            h.documento_id.id for h in self.browse(cr, uid, ids, context)
        ))

    _columns = {
        'perfil_id': fields.many2one('ud.perfil', u'Inscrição', required=True, ondelete='restrict'),
        'discente_id': fields.related('perfil_id', 'ud_papel_id', type='many2one', relation='ud.employee', readonly=True,
                                      string=u'Discente'),
        'dados_bancarios_id': fields.many2one('ud.dados.bancarios', u'Dados Bancários', ondelete='restrict',
                                              domain="[('ud_conta_id', '=', discente_id)]"),
        'tutor': fields.boolean(u'Tutor?', help=u'Indica se o discente é um tutor, caso contrário, ele é um monitor'),
        'disciplina_id': fields.many2one('ud_monitoria.disciplina', u'Disciplina', required=True, ondelete='restrict'),
        'semestre_id': fields.related('disciplina_id', 'bolsas_curso_id', 'semestre_id', type='many2one',
                                      relation='ud_monitoria.semestre', string=u'Semestre', ondelete='restrict'),
        'curso_id': fields.related('disciplina_id', 'bolsas_curso_id', type='many2one', string=u'Curso',
                                   relation='ud_monitoria.bolsas_curso', ondelete='restrict'),
        'orientador_id': fields.related('disciplina_id', 'orientador_id', type='many2one', relation='ud.employee', string=u'Orientador'),
        'frequencia_ids': fields.one2many('ud_monitoria.frequencia', 'documentos_id', u'Frequências'),
        'declaracao': fields.binary(u'Declaração'),
        'certificado': fields.binary(u'Certificado'),
        'relatorio': fields.binary(u'Relatório Final'),
        'horario_ids': fields.one2many('ud_monitoria.horario', 'documento_id', u'Horários'),
        'ch': fields.function(calcula_ch, type='char', string=u'Carga horária', help=u'Carga horária total', store={
            'ud_monitoria.horario': (horas_alteradas, ['hora_i', 'hora_f'], 10),
            # 'ud_monitoria.documentos_discente': (lambda *args, **kwargs: args[3], ['horario_ids'], 10),
        }),
        'informacao': fields.text(u'Informações'),
        'state': fields.selection(_STATES, u'Status', required=True),
        'is_active': fields.boolean('Ativo?'),
        # Campos de Controle
        'frequencia_controle': fields.function(frequencia_controle, type='boolean', string=u'Controle'),
        'certificado_nome': fields.char(u'Nome Certificado'),
        'declaracao_nome': fields.char(u'Nome Declaração'),
    }
    _defaults = {
        'is_active': True,
    }
    _sql_constraints = [
        ('disciplina_discente_unico', 'unique(disciplina_id,discente_id)',
         u'Não é permitido vincular a mesma disciplina de um semestre para o mesmo discente.')
    ]
    _constraints = [
        (lambda cls, *args, **kwargs: cls.valida_vagas_bolsista(*args, **kwargs),
         u'Não há vagas para adicionar o discente como bolsista.', [u'Disciplinas']),
        (lambda cls, *args, **kwargs: cls.valida_vagas_n_bolsista(*args, **kwargs),
         u'Não há vagas disponíveis para adicionar o discente como NÃO bolsista.', [u'Disciplinas']),
    ]

    # Métodos Sobrescritos
    def name_get(self, cr, uid, ids, context=None):
        """
        === Sobrescrita do método osv.Model.name_get
        Define a forma de visualização desse modelo em campos many2one.
        """
        return [
            (doc.id, doc.discente_id.name)
            for doc in self.browse(cr, uid, ids, context)
            ]

    def name_search(self, cr, uid, name='', args=None, operator='ilike', context=None, limit=100):
        """
        === Sobrescrita do método osv.Model.name_search
        Define a forma de pesquisa desse modelo em campos many2one.
        """
        pessoas = self.pool.get("ud.employee").search(cr, SUPERUSER_ID, [("name", operator, name)], context=context)
        perfis = self.pool.get("ud.perfil").search(
            cr, SUPERUSER_ID, ['|', ("matricula", operator, name), ("ud_papel_id", "in", pessoas)], context=context
        )
        args = [("perfil_id", "in", perfis)] + (args or [])
        ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)

    def create(self, cr, uid, vals, context=None):
        """
        === Extensão do método osv.Model.create
        Caso não tenha sido inserido nenhum dado bancário, busca da inscrição do discente, cria um relatório final para
        a disciplina e discente correspondentes e adiciona o mesmo no grupo de segurança de monitores.
        """
        if not vals.get("dados_bancarios_id", False) and vals.get("inscricao_id", False):
            insc = self.pool.get("ud_monitoria.inscricao").browse(cr, uid, vals.pop("inscricao_id"), context)
            vals["dados_bancarios_id"] = insc.dados_bancarios_id.id
        res = super(DocumentosDiscente, self).create(cr, uid, vals, context)
        if vals.get('is_active', False):
            self.add_grupo_monitor(cr, uid, res, context)
        return res

    def unlink(self, cr, uid, ids, context=None):
        """
        === Extensão do método osv.Model.unlink
        Remove os discentes envolvidos do grupo de segurança e verifica se há algum perfil de discente como bolsista
        de monitoria para remover os dados referentes a mesma.
        """
        perfil_model = self.pool.get("ud.perfil")
        perfis = set()
        perfis_bolsa = set()
        for doc in self.browse(cr, uid, ids, context):
            if doc.state == "bolsista" and doc.is_active and doc.perfil_id.tipo_bolsa == "m":
                perfis_bolsa.add(doc.perfil_id.id)
            perfis.add(doc.perfil_id.id)
        super(DocumentosDiscente, self).unlink(cr, uid, ids, context)
        if perfis:
            self.remove_grupo_monitor(cr, uid, perfis=list(perfis), context=context)
        if perfis_bolsa:
            perfil_model.write(cr, SUPERUSER_ID, list(perfis),
                               {"is_bolsista": False, "perfis_bolsa": False, "valor_bolsa": False}, context)
        return True

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        """
        === Extensão do método osv.Model.search
        Se utilizado o valor "filtrar_discente" em context, filtra os documentos do discente.
        """
        if (context or {}).get("filtrar_discente", False):
            pessoas = self.pool.get("ud.employee").search(cr, SUPERUSER_ID, [("user_id", "=", uid)], context=context)
            if not pessoas:
                return []
            perfis = self.pool.get("ud.perfil").search(cr, SUPERUSER_ID, [("ud_papel_id", "in", pessoas)], context=context)
            args = (args or []) + [("perfil_id", "in", perfis)]
        return super(DocumentosDiscente, self).search(cr, uid, args, offset, limit, order, context, count)

    # Validadores
    def valida_vagas_bolsista(self, cr, uid, ids, context=None):
        """
        Verifica se há vagas para novos discentes bolsistas.
        """
        for doc in self.browse(cr, uid, ids, context):
            if doc.is_active and doc.state == "bolsista":
                args = [('id', '!=', doc.id), ("disciplina_id", "=", doc.disciplina_id.id), ("is_active", "=", True),
                        ("state", "=", "bolsista")]
                qtd = self.search_count(cr, uid, args, context=context)
                if doc.disciplina_id.bolsas <= qtd:
                    return False
        return True

    def valida_vagas_n_bolsista(self, cr, uid, ids, context=None):
        """
        Verifica se há vagas para novos discentes não bolsistas.
        """
        for doc in self.browse(cr, uid, ids, context):
            if doc.is_active and doc.state == "n_bolsista":
                args = [('id', '!=', doc.id), ("disciplina_id", "=", doc.disciplina_id.id), ("is_active", "=", True),
                        ("state", "=", "n_bolsista")]
                monitores = self.search_count(cr, uid, args + [("tutor", "=", False)], context=context)
                tutores = self.search_count(cr, uid, args + [("tutor", "=", True)], context=context)
                if doc.disciplina_id.monitor_s_bolsa <= monitores or doc.disciplina_id.tutor_s_bolsa <= tutores:
                    return False
        return True

    # Métodos de manipulação do grupo de segurança
    def add_grupo_monitor(self, cr, uid, ids, context=None):
        """
        Adiciona discente do documento ao groupo de segurança.

        :raise osv.except_osv: Se não houver um usuário vinculado ao perfil.
        """
        if isinstance(ids, (int, long)):
            ids = [ids]
        group = self.pool.get("ir.model.data").get_object(
            cr, SUPERUSER_ID, "ud_monitoria", "group_ud_monitoria_monitor", context
        )
        for doc in self.browse(cr, uid, ids, context):
            if not doc.discente_id.user_id:
                raise osv.except_osv(
                    "Usuário não encontrado",
                    "O registro no núcleo do atual discente não possui login de usuário.")
            group.write({"users": [(4, doc.discente_id.user_id.id)]})

    def remove_grupo_monitor(self, cr, uid, ids=None, perfis=None, context=None):
        """
        Remove discente do grupo de segurança de monitores caso não possua mais vínculos com DocumentosDiscente.

        :param ids: ID ou lista de IDs do modelo atual.
        :param perfis: Lista de IDs de perfils.
        """
        if isinstance(ids, (int, long)):
            ids = [ids]
        group = self.pool.get("ir.model.data").get_object(
            cr, SUPERUSER_ID, "ud_monitoria", "group_ud_monitoria_monitor", context
        )
        perfil_model = self.pool.get('ud.perfil')
        if perfis:
            sql = '''
            SELECT
                usu.id
            FROM
                %(per)s per LEFT JOIN %(doc)s doc ON (doc.perfil_id = per.id)
                    INNER JOIN %(pes)s pes ON (per.ud_papel_id = pes.id)
                        INNER JOIN %(res)s res ON (pes.resource_id = res.id)
                            INNER JOIN %(usu)s usu ON (res.user_id = usu.id)
            WHERE
                per.id in (%(perfis)s) AND doc.id is null;
            ''' % {
                'doc': self._table,
                'per': perfil_model._table,
                'pes': self.pool.get('ud.employee')._table,
                'res': self.pool.get('resource.resource')._table,
                'usu': self.pool.get('res.users')._table,
                'perfis': str(perfis).lstrip('([').rstrip(']),').replace('L', '')
            }
            cr.execute(sql)
            res = cr.fetchall()
            if res:
                for usuario in res:
                    group.write({"users": [(3, usuario[0])]})
        if ids:
            for doc in self.browse(cr, uid, ids, context):
                perfis = perfil_model.search_count(cr, SUPERUSER_ID, [('ud_papel_id', '=', doc.discente_id.id)])
                if not self.search_count(cr, SUPERUSER_ID, [('perfil_id', 'in', perfis)]):
                    group.write({"users": [(3, doc.discente_id.user_id.id)]})

    # Ações de Botões
    def habilitar(self, cr, uid, ids, context=None):
        for doc in self.browse(cr, uid, ids, context):
            if doc.state in ['reserva', 'desligado']:
                raise osv.except_osv(
                    u'Ação Indisponível',
                    u'Documentos no cadastro de reserva ou desligados não podem ser habilitados por essa função.'
                )
            if not doc.disciplina_id.is_active:
                raise osv.except_osv(
                    u'Ação Indisponível', u'Somente é possível habilitar esse documento se sua disciplina estiver ativa.'
                )
        return self.write(cr, uid, ids, {'is_active': True})

    def desabilitar(self, cr, uid, ids, context=None):
        """
        Inativa o documento do discente.

        :raise osv.except_osv: Se disciplina ainda ativa; Se documento ativo e não possui frequências, relatórios, uma
                               das frequências ainda está em análise ou não há uma frequência aceita para os meses
                               correspondentes.
        """
        for doc in self.browse(cr, uid, ids, context):
            if doc.disciplina_id.is_active:
                raise osv.except_osv(u"Ação Indisponível",
                                     u"O documento não pode ser desabilitado enquanto a disciplina estiver ativa.")
            if doc.is_active:
                freqs = {}
                if len(doc.frequencia_ids) == 0:
                    raise osv.except_osv(
                        u"Ação Indisponível",
                        u"Não é possível finalizar o documento enquanto não houver ao menos uma frequência."
                    )
                if len(doc.relatorio_ids) == 0:
                    raise osv.except_osv(
                        u"Ação Indisponível",
                        u"Não é possível finalizar o documento enquanto não houver ao menos um relatório."
                    )
                for freq in doc.frequencia_ids:
                    if freq.state == "analise":
                        raise osv.except_osv(u"Ação Indisponível", u"Você não pode finalizar documentos enquanto houver"
                                                                   u" frequências em análise.")
                    freqs[freq.mes] = freqs[freq.mes] or freq.state == "aceito"
                if not all(freqs.values()):
                    raise osv.except_osv(u"Ação Indisponível", u"Você não pode finalizar documentos enquanto não houver"
                                                               u" ao menos uma frequência aceita para cada mês")
        return self.write(cr, uid, ids, {"is_active": False})

    def reserva_para_bolsista(self, cr, uid, ids, context=None):
        """
        Muda o status do documento do discente de reserva para bolsista habilitando o registro. O registro
        do orientador será criado se não existir.

        :raise osv.except_osv: Caso sua disciplina esteja inativa ou caso haja algum documento com status diferente de
                               "reserva".
        """
        if len(set(ids)) != self.search_count(cr, uid, [("id", "in", ids), ("state", "=", "reserva")], context):
            raise osv.except_osv(
                u"O discente deve está no cadastro de reserva",
                u"Esse recuros pode ser utilzado apenas em registros de discentes no cadastro de reserva"
            )
        doc_orientador_model = self.pool.get("ud_monitoria.documentos_orientador")
        for doc in self.browse(cr, uid, ids, context):
            if not doc.disciplina_id.is_active:
                raise osv.except_osv(u"Ação Indisponível",
                                     u"Não é possível retirar um discente do cadastro de reserva se sua disciplina está inativa.")
            doc_orientador = doc_orientador_model.search_count(cr, uid, [("disciplina_id", "=", doc.disciplina_id.id)])
            if not doc_orientador:
                doc_orientador_model.create(cr, SUPERUSER_ID, {
                    "disciplina_id": doc.disciplina_id.id, 'perfil_id': doc.disciplina_id.perfil_id.id
                }, context)
            doc_orientador = doc_orientador_model.search_count(cr, uid, [("id", "in", doc_orientador), ('is_active', '=', False)])
            if doc_orientador:
                doc_orientador_model.write(cr, SUPERUSER_ID, doc_orientador, {'is_active': True})
        return self.write(cr, uid, ids, {"state": 'bolsista', 'is_active': True}, context)

    def reserva_para_n_bolsista(self, cr, uid, ids, context=None):
        """
        Retira do cadastro de reserva, muda o status para "Não bolsista" e habilida o documento do discente. O registro
        do orientador será criado se não existir.

        :raise osv.except_osv: Caso sua disciplina esteja inativa ou caso haja algum documento com status diferente de
                               "reserva".
        """
        ids = list(set(ids))
        if len(set(ids)) != self.search_count(cr, uid, [("id", "in", ids), ("state", "=", "reserva")], context):
            raise osv.except_osv(
                u"O discente deve está no cadastro de reserva",
                u"Esse recuros pode ser utilzado apenas em registros de discentes no cadastro de reserva"
            )
        doc_orientador_model = self.pool.get("ud_monitoria.documentos_orientador")
        for doc in self.browse(cr, uid, ids, context):
            if not doc.disciplina_id.is_active:
                raise osv.except_osv(u"Ação Indisponível",
                                     u"Não é possível retirar um discente do cadastro de reserva se sua disciplina está inativa.")
            doc_orientador = doc_orientador_model.search_count(cr, uid, [("disciplina_id", "=", doc.disciplina_id.id)])
            if not doc_orientador:
                doc_orientador_model.create(cr, SUPERUSER_ID, {
                    "disciplina_id": doc.disciplina_id.id, 'perfil_id': doc.disciplina_id.perfil_id.id
                }, context)
            doc_orientador = doc_orientador_model.search_count(cr, uid, [("id", "in", doc_orientador), ('is_active', '=', False)])
            if doc_orientador:
                doc_orientador_model.write(cr, SUPERUSER_ID, doc_orientador, {'is_active': True})
        return self.write(cr, uid, ids, {"state": 'n_bolsista', 'is_active': True}, context)


class Horario(osv.Model):
    _name = "ud_monitoria.horario"
    _description = u"Horário do monitori (UD)"
    _order = "CASE WHEN dia = 'seg' THEN 1 " \
             "WHEN dia = 'ter' THEN 2 " \
             "WHEN dia = 'qua' THEN 3 " \
             "WHEN dia = 'qui' THEN 4 " \
             "WHEN dia = 'sex' THEN 5 " \
             "WHEN dia = 'sab' THEN 6 " \
             "ELSE 10 " \
             "END Asc, hora_i asc"
    _rec_name = "dia"
    _DIAS = [("seg", u"Segunda"), ("ter", u"Terça"), ("qua", u"Quarta"), ("qui", u"Quinta"), ("sex", u"Sexta"), ("sab", u"Sábado")]

    # Método para campo de função
    def calc_ch(self, cr, uid, ids, campo, args, context=None):
        """
        Calcula o número de horas entre a hora inicial e final.
        """
        res = {}
        for horario in self.browse(cr, uid, ids, context=context):
            horas = divmod(
                (datetime.strptime(horario.hora_f, "%H:%M") - datetime.strptime(horario.hora_i, "%H:%M")).seconds, 3600
            )
            minutos = divmod(horas[1], 60)
            res[horario.id] = "%s%s%s" % (
                horas[0] and "%i hora%s" % (horas[0], "s" if horas[0] > 1 else "") or "",
                horas[0] and minutos[0] and " e " or "",
                minutos[0] and "%i minuto%s" % (minutos[0], "s" if minutos[0] > 1 else "") or "",
            )
        return res

    _columns = {
        "dia": fields.selection(_DIAS, u"Dia", required=True),
        "hora_i": fields.char(u"Hora Inicial", required=True, size=5),
        "hora_f": fields.char(u"Hora Final", required=True, size=5),
        "observacoes": fields.html(u"Observações"),
        "ch": fields.function(calc_ch, type="char", string=u"Carga horária", store={
            "ud_monitoria.horario": (lambda cls, cr, uid, ids, context=None: ids, ["hora_i", "hora_f"], 10),
        }),
        "documento_id": fields.many2one("ud_monitoria.documentos_discente", u"Documentos", ondelete="cascade",
                                        help=u"Documentos de um Discente", invisible=True)
    }

    _constraints = [
        (
            lambda cls, *args, **kwargs: cls.valida_hora(*args, **kwargs),
            u"A hora inicial e/ou final não estão corretas ou não definem um intervalo válido",
            ["Hora Inicial", "Hora Final"]
        ),
    ]

    # Métodos sobrescritos
    def _check_qorder(self, word):
        """
        === Sobrescrita do método osv.Model._check_qorder
        Adaptação para as novas modificações da validação da cláusula de ordenação condicional.
        """
        if not regex_order.match(word):
            raise orm.except_orm(_('AccessError'),
                                 u"A ordenação do Horário não está de acordo com o padrão. Use apenas o nome do campo "
                                 u"ou um conjunto de casos seguidos, ou não, de ASC/DESC!")
        return True

    def _generate_order_by(self, order_spec, query):
        """
        === Extensão do método osv.Model._generate_order_by
        Geração personalizada da cláusula SQL "ORDER BY" para suportar ordenação condicional "CASE ... WHEN ... THEN ...".
        """
        inserir = lambda valores: " ".join(map(lambda v: "WHEN {}.{} = {} THEN {}".format(self._table, *v), valores))
        clausulas = ""
        order_spec = order_spec or self._order
        outros = []
        ord_elementos = []
        if order_spec:
            self._check_qorder(order_spec)
            for part in order_spec.split(","):
                part = part.strip(" ").strip(",").strip(" ")
                if len(regex_espacos.split(part)) > 2:
                    r = regex_regra.match(part)
                    if r:
                        regra = "CASE {clau} ELSE {ord} END {dir}".format(clau=inserir(regex_clausula.findall(part)),
                                                                          ord=r.group("ord"),
                                                                          dir=r.group("dir") or "")
                        ord_elementos.append(regra)
                else:
                    outros.append(part)
            res = super(Horario, self)._generate_order_by(",".join(outros), query)
            if ord_elementos:
                clausulas = ",".join(ord_elementos)
            if clausulas or res:
                clausulas = " ORDER BY " + ",".join([(clausulas or ""), (res and res[10:] or "")]).strip(",")
        return clausulas or ''

    # Método de validação
    def valida_hora(self, cr, uid, ids, context=None):
        """
        Verifica se o padrão de horas inseridas estão corretas com horas de 0 à 23 e minutos de 0 até 59 e se a hora
        inicial ocorre antes da final.
        """
        for horario in self.read(cr, uid, ids, ["hora_i", "hora_f"], context=context, load="_classic_write"):
            if not regex_hora.match(horario["hora_i"]) or not regex_hora.match(horario["hora_f"]):
                return False
            elif not datetime.strptime(horario["hora_i"], "%H:%M") < datetime.strptime(horario["hora_f"], "%H:%M"):
                return False
            h, m = horario["hora_i"].split(":")
            if int(h) > 23 or int(m) > 59:
                return False
            h, m = horario["hora_f"].split(":")
            if int(h) > 23 or int(m) > 59:
                return False
        return True


class Frequencia(osv.Model):
    _name = "ud_monitoria.frequencia"
    _description = u"Frequência do monitor/tutor UD)"
    _order = "state"

    _STATES = [("analise", u"Em Análise"), ("rejeitado", u"Rejeitado"), ("aceito", u"Aceito")]

    _columns = {
        "mes": fields.selection(_MESES, u"Mês", required=True),
        "ano": fields.integer(u"Ano", required=True),
        "state": fields.selection(_STATES, u"Status"),
        "frequencia": fields.binary(u"Frequência", required=True),
        "frequencia_nome": fields.char(u"Nome da Frequência"),
        "documentos_id": fields.many2one("ud_monitoria.documentos_discente", u"Documentos", ondelete="cascade",
                                         help=u"Documentos de um Discente", invisible=True),
    }

    _defaults = {
        "ano": datetime.today().year,
    }

    # Validadores
    def valida_status(self, cr, uid, ids, context=None):
        """
        Verifica se há mais de uma frequência com status "analise", "aceito" ou uma com status "analise" e outra "aceito".
        """
        for freq in self.browse(cr, uid, ids, context):
            analise, aceita = 0, 0
            for f in freq.documentos_id.frequencia_ids:
                if freq.mes == f.mes:
                    if f.state == "analise":
                        analise += 1
                    elif f.state == "aceito":
                        aceita += 1
            if analise and aceita or analise > 1 or aceita > 1:
                return False
        return True

    def valida_data(self, cr, uid, ids, context=None):
        """
        Verifica se ainda está dentro do prazo para inserção de novas frequências.
        """
        hoje = datetime.utcnow().date()
        for freq in self.browse(cr, SUPERUSER_ID, ids, context):
            data = datetime.strptime(freq.documentos_id.disciplina_id.semestre_id.data_i_frequencia, DEFAULT_SERVER_DATE_FORMAT).date()
            if not (data <= hoje <= (data + timedelta(freq.documentos_id.disciplina_id.semestre_id.intervalo_frequencia))):
                return False
        return True

    _constraints = [
        (valida_status, u"Não é possível criar novas frequências para meses que possuam outros registros em análise ou aceitos.", [u"Mês"]),
        (valida_data, u"Inclusão de novas frequências deve está dentro do prazo.", [u"Frequência"]),
    ]

    def create(self, cr, uid, vals, context=None):
        """
        === Extensão do método osv.Model.create
        Atribui o statuso ao valor "analise".
        """
        vals["state"] = "analise"
        return super(Frequencia, self).create(cr, uid, vals, context)

    def botao_aceitar(self, cr, uid, ids, context=None):
        """
        Altera o status para "aceito".
        """
        for freq in self.browse(cr, uid, ids, context):
            args = [
                ('state', '=', 'rejeitado'), ('mes', '=', freq.mes), ('ano', '=', freq.ano)
            ]
            freq_ids = self.search(cr, uid, args)
            if freq_ids:
                self.unlink(cr, SUPERUSER_ID, freq_ids)
            if freq.documentos_id.orientador_id.user_id.id != uid and not self.user_has_groups(cr, uid, 'ud_monitoria.group_ud_monitoria_coordenador'):
                raise orm.except_orm(u'Permissão Negada!',
                                     u'Você não possui permissão para validar frequências desse discente')
        return self.write(cr, uid, ids, {"state": "aceito"}, context)

    def botao_rejeitar(self, cr, uid, ids, context=None):
        """
        Altera o status para "rejeitado".
        """
        for freq in self.browse(cr, uid, ids, context):
            if freq.documentos_id.orientador_id.user_id.id != uid and not self.user_has_groups(cr, uid, 'ud_monitoria.group_ud_monitoria_coordenador'):
                raise orm.except_orm(u'Permissão Negada!',
                                     u'Você não possui permissão para validar frequências desse discente')
        return self.write(cr, uid, ids, {"state": "rejeitado"}, context)
