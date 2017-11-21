# coding: utf-8
from datetime import datetime, timedelta
from re import compile, IGNORECASE
from openerp import SUPERUSER_ID
from openerp.osv import osv, fields, orm
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.translate import _

regex_hora = compile("^[0-2][0-9]:[0-5][0-9]$")
regex_order = compile(
    "^((?:(?:CASE(?: WHEN \w+ *= *'\w+' THEN \d+)+ ELSE \d+ END)|(?:\w+))(?: (?:(?:asc)|(?:desc)))?)(, *"
    "(?:(?:CASE(?: WHEN \w+ *= *'\w+' THEN \d+)+ ELSE \d+ END)|(?:\w+))(?: (?:(?:asc)|(?:desc)))?)?$", IGNORECASE
)
regex_regra = compile("CASE .+ ELSE (?P<ord>\d+) END (?P<dir>(?:asc)|(?:desc))?", IGNORECASE)
regex_clausula = compile("WHEN (?P<campo>\w+) *= *(?P<valor>'\w+') THEN (?P<ord>\d+)", IGNORECASE)
regex_espacos = compile("\s+")

_MESES = [("01", u"Janeiro"), ("02", u"Fevereiro"), ("03", u"Março"), ("04", u"Abril"), ("05", u"Maio"),
          ("06", u"Junho"), ("07", u"julho"), ("08", u"Agosto"), ("09", u"Setembro"), ("10", u"Outubro"),
          ("11", u"Novembro"), ("12", u"Dezembro")]


class DocumentosDiscente(osv.Model):
    _name = "ud.monitoria.documentos.discente"
    _description = u"Documentos de monitoria do discente (UD)"
    _order = "is_active desc, disciplina_id, state, tutor"  # TODO: Verificar essa ordenação

    _STATES = [("reserva", u"Cadastro de Reserva"), ("n_bolsista", u"Não Bolsista"),
               ("bolsista", u"Bolsista"), ("desligado", u"Desligado(a)")]

    def calcula_ch(self, cr, uid, ids, campo, args, context=None):
        """
        Calcula a carga horária total que o discente atribuiu em seus horários de atendimento.
        """
        def converte(dt):
            horas = divmod(dt.seconds, 3600)
            minutos = divmod(horas[1], 60)
            return horas[0], minutos[0]

        def dif_horas(h):
            return datetime.strptime(h.hora_f, "%H:%M") - datetime.strptime(h.hora_i, "%H:%M")

        res = {}
        for doc in self.browse(cr, uid, ids, context=context):
            tempo = None
            for h in doc.horario_ids:
                tempo = tempo and tempo + dif_horas(h) or dif_horas(h)
            tempo = converte(tempo)
            # tempo = converte(sum([dif_horas(h) for h in doc.horario_ids]))
            res[doc.id] = "%s%s%s" % (
                tempo[0] and "%i hora%s" % (tempo[0], "s" if tempo[0] > 1 else "") or "",
                tempo[0] and tempo[1] and " e " or "",
                tempo[1] and "%i minuto%s" % (tempo[1], "s" if tempo[1] > 1 else "") or "",
            )
        return res

    def status_relatorios(self, cr, uid, ids, campo, args, context=None):
        """
        Verifica se há ao menos um relatório final aceito.
        """
        res = {}
        for doc in self.browse(cr, uid, ids, context):
            for rel in doc.relatorio_ids:
                if rel.state == "aceito":
                    res[doc.id] = True
                    break
        return res

    def frequencia_controle(self, cr, uid, ids, campo, args, context=None):
        """
        Define se o discente pode adicionar novas frequências.
        """
        res = {}
        hoje = datetime.utcnow().date()
        for doc in self.browse(cr, SUPERUSER_ID, ids, context):
            data = datetime.strptime(doc.disciplina_id.semestre_id.data_i_frequencia, DEFAULT_SERVER_DATE_FORMAT).date()
            res[doc.id] = data <= hoje <= (data + timedelta(doc.disciplina_id.semestre_id.intervalo_frequencia))
        return res

    def horas_alteradas(self, cr, uid, ids, context=None):
        """
        Define quais documentos deverão ter sua carga horária atualizada.
        """
        return [
            h.documento_id.id for h in self.browse(cr, uid, ids, context)
            ]

    def valida_vagas_bolsista(self, cr, uid, ids, context=None):
        """
        Verifica se há vagas para novos discentes bolsistas.
        """
        for doc in self.browse(cr, uid, ids, context):
            if doc.is_active and doc.state == "bolsista":
                args = [("disciplina_id", "=", doc.disciplina_id.id), ("is_active", "=", True), ("state", "=", "bolsista")]
                discentes = self.search_count(cr, uid, args, context=context)
                for pont in doc.inscricao_id.pontuacoes_ids:
                    if pont.disciplina_id.disciplina_id.id == doc.disciplina_id.disciplina_id.id:
                        if discentes > pont.disciplina_id.bolsas:
                            return False
                        break
        return True

    def valida_vagas_n_bolsista(self, cr, uid, ids, context=None):
        """
        Verifica se há vagas para novos discentes não bolsistas.
        """
        for doc in self.browse(cr, uid, ids, context):
            if doc.is_active and doc.state == "n_bolsista":
                args = [("disciplina_id", "=", doc.disciplina_id.id), ("is_active", "=", True), ("state", "=", "n_bolsista")]
                monitores = self.search_count(cr, uid, args + [("tutor", "=", False)], context=context)
                tutores = self.search_count(cr, uid, args + [("tutor", "=", True)], context=context)
                for pont in doc.inscricao_id.pontuacoes_ids:
                    if pont.disciplina_id.disciplina_id.id == doc.disciplina_id.disciplina_id.id:
                        if doc.tutor and tutores > pont.disciplina_id.tutor_s_bolsa or monitores > pont.disciplina_id.monitor_s_bolsa:
                            return False
                        break
        return True

    _columns = {
        "inscricao_id": fields.many2one("ud.monitoria.inscricao", u"Inscrição", required=True, ondelete="restrict"),
        "discente_id": fields.related("inscricao_id", "discente_id", type="many2one", relation="ud.employee", readonly=True, string=u"Discente"),
        "dados_bancarios_id": fields.many2one("ud.dados.bancarios", u"Dados Bancários", ondelete="restrict",
                                              domain="[('ud_conta_id', '=', discente_id)]"),
        "disciplina_id": fields.many2one("ud.monitoria.disciplina", u"Disciplina", required=True, ondelete="restrict"),
        "orientador_id": fields.related("disciplina_id", "orientador_id", type="many2one", relation="ud.employee", string=u"Orientador"),
        "tutor": fields.boolean(u"Tutor?", help=u"Indica se o discente é um tutor, caso contrário, ele é um monitor"),
        "frequencia_ids": fields.one2many("ud.monitoria.frequencia", "documentos_id", u"Frequências"),
        "declaracao": fields.binary(u"Declaração"),
        "certificado": fields.binary(u"Certificado"),
        "relatorio_ids": fields.one2many("ud.monitoria.relatorio", "documentos_id", u"Relatórios"),
        "horario_ids": fields.one2many("ud.monitoria.horario", "documento_id", u"Horários"),
        "state": fields.selection(_STATES, u"Status", required=True),
        "is_active": fields.boolean("Ativo?"),
        "ch": fields.function(calcula_ch, type="char", string=u"Carga horária", help=u"Carga horária total", store={
            "ud.monitoria.horario": (horas_alteradas, ["hora_i", "hora_f"], 10),
            "ud.monitoria.documentos.discente": (lambda *args, **kwargs: args[3], ["hora_i", "hora_f"], 10),
        }),
        # Campos de Controle
        "frequencia_controle": fields.function(frequencia_controle, type="boolean", string=u"Controle"),
        "certificado_nome": fields.char(u"Nome Certificado"),
        "declaracao_nome": fields.char(u"Nome Declaração"),
        "relatorios_ok": fields.function(status_relatorios, type="boolean", string=u"Status dos Relatórios"),
    }

    _defaults = {
        "is_active": True,
    }

    _sql_constraints = [
        ("disciplina_discente_unico", "unique(disciplina_id,discente_id)",
         u"Não é permitido vincular a mesma disciplina de um semestre para o mesmo discente.")
    ]

    _constraints = [
        (valida_vagas_bolsista, u"Não há vagas para adicionar o discente como bolsista.", [u"Disciplinas"]),
        (valida_vagas_n_bolsista, u"Não há vagas disponíveis para adicionar o discente como NÃO bolsista.", [u"Disciplinas"])
    ]

    def name_get(self, cr, uid, ids, context=None):
        """
        === Sobrescrita do método osv.Model.name_get
        Define a forma de visualização desse modelo em campos many2one.
        """
        return [
            (doc["id"], doc["discente_id"][1])
            for doc in self.read(cr, uid, ids, ["discente_id"], context=context)
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
        inscricoes = self.pool.get("ud.monitoria.inscricao").search(cr, uid, [("perfil_id", "in", perfis)], context=context)

        args = [("inscricao_id", "in", inscricoes)] + (args or [])
        ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)

    def create(self, cr, uid, vals, context=None):
        """
        === Extensão do método osv.Model.create
        Caso não tenha sido inserido nenhum dado bancário, busca da inscrição do discente, cria um relatório final para
        a disciplina e discente correspondentes e adiciona o mesmo no grupo de segurança de monitores.
        """
        if not vals.get("dados_bancarios_id", False) and vals.get("inscricao_id", False):
            insc = self.pool.get("ud.monitoria.inscricao").browse(cr, uid, vals["inscricao_id"], context)
            vals["dados_bancarios_id"] = insc.dados_bancarios_id.id
        res = super(DocumentosDiscente, self).create(cr, uid, vals, context)
        self.relatorio_fim_correspondente(cr, SUPERUSER_ID, res, context)
        self.add_grupo_monitor(cr, uid, res, context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        """
        === Extensão do método osv.Model.write
        Se adicionado novas frequências e não houver relatórios do mês correspondente para elas, novos serão criados e
        vinculados ao discente correspondente.
        """
        super(DocumentosDiscente, self).write(cr, uid, ids, vals, context)
        if "frequencia_ids" in vals:
            args = []
            meses = set()
            clausulas = ""
            for freq in vals["frequencia_ids"]:
                if freq[0] == 0 and freq[2].get("ano", None) and freq[2].get("mes", None):
                    if clausulas:
                        clausulas += " OR mes = '{}' AND ano = '{}'".format(freq[2]["mes"], freq[2]["ano"])
                        args += ["|", ("mes", "=", freq[2]["mes"]), ("ano", "=", freq[2]["ano"])]
                    else:
                        clausulas = "mes = '{}' AND ano = '{}'".format(freq[2]["mes"], freq[2]["ano"])
                        args += [("mes", "=", freq[2]["mes"]), ("ano", "=", freq[2]["ano"])]
                    meses.add((freq[2]["mes"], freq[2]["ano"]))
            if meses:
                rel_model = self.pool.get("ud.monitoria.relatorio.final.disc")
                rfd_model = self.pool.get("ud.monitoria.rfd.mes")
                sql = "SELECT mes, ano FROM {rfd} WHERE relatorio_id = {rel} AND ({clausulas});"
                for rel in rel_model.search(cr, SUPERUSER_ID, [("doc_discente_id", "in", ids)]):
                    cr.execute(sql.format(rfd=rfd_model._table, rel=rel, clausulas=clausulas))
                    res = meses.difference(cr.fetchall())
                    if res:
                        for mes in res:
                            rfd_model.create(cr, SUPERUSER_ID, {"mes": mes[0], "ano": mes[1], "relatorio_id": rel})
        return True

    def unlink(self, cr, uid, ids, context=None):
        """
        === Extensão do método osv.Model.unlink
        Remove os discentes envolvidos do grupo de segurança e verifica se há algum perfil de discente como bolsista
        de monitoria para remover os dados referentes a mesma.
        """
        perfil_model = self.pool.get("ud.perfil")
        perfis = set()
        for doc in self.browse(cr, uid, ids, context):
            if doc.state == "bolsista" and doc.is_active and doc.inscricao_id.perfil_id.tipo_bolsa == "m":
                perfis.add(doc.inscricao_id.perfil_id.id)
        self.remove_grupo_monitor(cr, uid, ids, context)
        super(DocumentosDiscente, self).unlink(cr, uid, ids, context)
        if perfis:
            perfil_model.write(cr, SUPERUSER_ID, list(perfis),
                               {"is_bolsista": False, "tipo_bolsa": False, "valor_bolsa": False}, context)
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
            inscricoes = self.pool.get("ud.monitoria.inscricao").search(cr, uid, [("perfil_id", "in", perfis)], context=context)
            args = (args or []) + [("inscricao_id", "in", inscricoes)]
        return super(DocumentosDiscente, self).search(cr, uid, args, offset, limit, order, context, count)

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

    def remove_grupo_monitor(self, cr, uid, ids, context=None):
        """
        Remove discente do grupo de segurança de monitores caso não possua mais vínculos do gênero.
        """
        if isinstance(ids, (int, long)):
            ids = [ids]
        group = self.pool.get("ir.model.data").get_object(
            cr, SUPERUSER_ID, "ud_monitoria", "group_ud_monitoria_monitor", context
        )
        disciplina_model = self.pool.get("ud.monitoria.disciplina")
        continua = []
        for doc in self.browse(cr, uid, ids, context):
            if doc.discente_id.id not in continua:
                perfis = [p.id for p in doc.discente_id.papel_ids]
                if disciplina_model.search_count(cr, uid, [("perfil_id", "in", perfis)], context) > 1:
                    continua.append(doc.discente_id.id)
                elif doc.discente_id.user_id:
                    group.write({"users": [(3, doc.discente_id.user_id.id)]})

    def relatorio_fim_correspondente(self, cr, uid, id_doc, context):
        """
        Cria um registro de relatorio final de disciplina, caso não exista, e vincula com o documento informado.

        :param id_doc: ID de documento de discente.
        """
        rel_model = self.pool.get("ud.monitoria.relatorio.final.disc")
        rel_id = rel_model.search(cr, uid, [("doc_discente_id", "=", id_doc)], context=context)
        if not rel_id:
            rel_model.create(cr, uid, {"doc_discente_id": id_doc}, context)

    def finalizar(self, cr, uid, ids, context=None):
        """
        Inativa o documento do discente.

        :raise osv.except_osv: Se disciplina ainda ativa; Se documento ativo e não possui frequências, relatórios, uma
                               das frequências ainda está em análise ou não há uma frequência aceita para os meses
                               correspondentes.
        """
        for doc in self.browse(cr, uid, ids, context):
            if doc.disciplina_id.is_active:
                raise osv.except_osv(u"Ação Indisponível",
                                     u"O documento não pode ser finalizando enquanto a data da disciplina estiver em vigor")
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

    def tornar_n_bolsista(self, cr, uid, ids, context=None):
        """
        Muda o status para "Não bolsista" e habilida o documento do discente.

        :raise osv.except_osv: Caso sua disciplina esteja inativa.
        """
        context = context or {}
        doc_orientador_model = self.pool.get("ud.monitoria.documentos.orientador")
        for doc in self.browse(cr, uid, ids, context):
            if not doc.disciplina_id.is_active:
                raise osv.except_osv(u"Ação Indisponível",
                                     u"Não é possível retirar um discente do cadastro de reserva se sua disciplina está inativa.")
            if not doc_orientador_model.search_count(cr, uid, [("disciplina_id", "=", doc.disciplina_id.id)]):
                doc_orientador_model.create(
                    cr, SUPERUSER_ID, {"disciplina_id": doc.disciplina_id.id}, context
                )
        return self.write(cr, uid, ids, {"is_active": True, "state": "n_bolsista"})

    def reserva_para_bolsista(self, cr, uid, ids, context=None):
        """
        Muda o status do documento do discnete de reserva para bolsista.

        :raise osv.except_osv: Caso haja algum registro inativo ou com status diferente de "reserva".
        """
        if len(set(ids)) != self.search_count(cr, uid, [("id", "in", ids), ('is_active', '=', True), ("state", "=", "reserva")], context):
            raise osv.except_osv(
                u"Registro inativo ou fora da reserva",
                u"Esse recuros pode ser utilzado apenas em registros de discentes ativos e no cadastro de reserva"
            )
        return self.write(cr, uid, ids, {"state": 'bolsista'}, context)

    def reserva_para_n_bolsista(self, cr, uid, ids, context=None):
        """
        Muda o status do documento do discnete de reserva para não bolsista.

        :raise osv.except_osv: Caso haja algum registro inativo ou com status diferente de "reserva".
        """
        ids = list(set(ids))
        if len(set(ids)) != self.search_count(cr, uid, [("id", "in", ids), ('is_active', '=', True), ("state", "=", "reserva")], context):
            raise osv.except_osv(
                u"Registro inativo ou fora da reserva",
                u"Esse recuros pode ser utilzado apenas em registros de discentes ativos e no cadastro de reserva"
            )
        return self.write(cr, uid, ids, {"state": 'n_bolsista'}, context)


class Horario(osv.Model):
    _name = "ud.monitoria.horario"
    _description = u"Horário do monitori (UD)"
    _order = "CASE WHEN dia = 'seg' THEN 1 " \
             "WHEN dia = 'ter' THEN 2 " \
             "WHEN dia = 'qua' THEN 3 " \
             "WHEN dia = 'qui' THEN 4 " \
             "WHEN dia = 'sex' THEN 5 " \
             "WHEN dia = 'sab' THEN 6 " \
             "ELSE 10 " \
             "END Asc, hora_i asc"

    _DIAS = [("seg", u"Segunda"), ("ter", u"Terça"), ("qua", u"Quarta"), ("qui", u"Quinta"), ("sex", u"Sexta"),
             ("sab", u"Sábado")]

    _columns = {
        "dia": fields.selection(_DIAS, u"Dia", required=True),
        "hora_i": fields.char(u"Hora Inicial", required=True, size=5),
        "hora_f": fields.char(u"Hora Final", required=True, size=5),
        "observacoes": fields.html(u"Observações"),
        "ch": fields.function(
            lambda cls, *args, **kwargs: cls.calc_ch(*args, **kwargs),
            type="char", string=u"Carga horária", store={
                "ud.monitoria.horario": (lambda cls, cr, uid, ids, context=None: ids, ["hora_i", "hora_f"], 10),
            }
        ),
        "documento_id": fields.many2one("ud.monitoria.documentos.discente", u"Documentos", ondelete="cascade",
                                        help=u"Documentos de um Discente", invisible=True)
    }

    _rec_name = "dia"

    _constraints = [
        (
            lambda cls, *args, **kwargs: cls.valida_hora(*args, **kwargs),
            u"A hora inicial e/ou final não estão corretas ou não definem um intervalo válido",
            ["Hora Inicial", "Hora Final"]
        ),
    ]

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
        Geração personalizada da cláusula SQL "ORDER BY" para suportar ordenação condicional "WHERE ... CASE ... THEN ...".
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


class Relatorio(osv.Model):
    _name = "ud.monitoria.relatorio"
    _description = u"Relatório do Discente (UD)"
    _order = "CASE WHEN state = 'analise' THEN 1 "\
             "WHEN state = 'aceito' THEN 2 "\
             "WHEN state = 'aceito' THEN 2 "\
             "ELSE 10 "\
             "END Asc, create_date asc"

    _STATES = [("analise", u"Em Análise"), ("rejeitado", u"Rejeitado"), ("aceito", u"Aceito")]

    def valida_relatorios(self, cr, uid, ids, context=None):
        """
        Verifica se há mais de um relatório com status "analise", "aceito" ou um com status "analise" e outr "aceito".
        """
        for rel in self.browse(cr, uid, ids, context):
            analise, aceito = 0, 0
            for r in rel.documentos_id.relatorio_ids:
                if r.state == "analise":
                    analise += 1
                elif r.state == "aceito":
                    aceito += 1
            if analise and aceito or analise > 1 or aceito > 1:
                return False
        return True

    _columns = {
        "id": fields.integer("ID", readonly=True, invisible=True),
        "relatorio_nome": fields.char(u"Nome Relatório", required=True, help=u"Relatório do discente"),
        "relatorio": fields.binary(u"Relatório", required=True, help=u"Relatório do discente"),
        "parecer_nome": fields.char(u"Nome Parecer", help=u"Parecer do Professor Orientador"),
        "parecer": fields.binary(u"Parecer", help=u"Parecer do Professor Orientador"),
        "state": fields.selection(_STATES, u"Status"),
        "info": fields.text(u"Informações", help=u"Informações Adicionais"),
        "create_date": fields.datetime(u"Data de Criação", readonly=True),
        "write_date": fields.datetime(u"Data de Atualização", readonly=True),
        "documentos_id": fields.many2one("ud.monitoria.documentos.discente", u"Documentos", ondelete="cascade",
                                        help=u"Documentos de um Discente", invisible=True),
    }

    _constraints = [
        (valida_relatorios, u"Não é possível criar novos relatórios enquanto houver outros registros em análise ou aceitos.", [u"Relatório"]),
    ]

    def create(self, cr, uid, vals, context=None):
        """
        === Extensão do método osv.Model.create
        Atribui o valor inicial do status para "analise".
        """
        vals["state"] = "analise"
        return super(Relatorio, self).create(cr, uid, vals, context)

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
        Geração personalizada da cláusula SQL "ORDER BY" para suportar ordenação condicional "WHERE ... CASE ... THEN ...".
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
            res = super(Relatorio, self)._generate_order_by(",".join(outros), query)
            if ord_elementos:
                clausulas = ",".join(ord_elementos)
            if clausulas or res:
                clausulas = " ORDER BY " + ",".join([(clausulas or ""), (res and res[10:] or "")]).strip(",")
        return clausulas or ''

    def alterar_status(self, cr, uid, ids, status, context=None):
        """
        Altera o status para algum valor.

        :raise osv.except_osv: Caso o relatório do professor não tenha sido anexado.
        """
        for relatorio in self.browse(cr, uid, ids, context):
            if not relatorio.parecer:
                raise osv.except_osv(u"Ação Inválida",
                                     u"Não é permitido alterar o status enquanto não anexar o parecer do professor")
        return self.write(cr, uid, ids, {"state": status}, context)

    def botao_aceitar(self, cr, uid, ids, context=None):
        """
        Altera o status para "aceito".
        """
        return self.alterar_status(cr, uid, ids, "aceito", context)

    def botao_rejeitar(self, cr, uid, ids, context=None):
        """
        Altera o status para "rejeitado".
        """
        return self.alterar_status(cr, uid, ids, "rejeitado", context)


class Frequencia(osv.Model):
    _name = "ud.monitoria.frequencia"
    _description = u"Frequência do monitor/tutor UD)"
    _order = "state"

    _STATES = [("analise", u"Em Análise"), ("rejeitado", u"Rejeitado"), ("aceito", u"Aceito")]

    _columns = {
        "mes": fields.selection(_MESES, u"Mês", required=True),
        "ano": fields.integer(u"Ano", required=True),
        "state": fields.selection(_STATES, u"Status"),
        "frequencia": fields.binary(u"Frequência", required=True),
        "frequencia_nome": fields.char(u"Nome da Frequência"),
        "documentos_id": fields.many2one("ud.monitoria.documentos.discente", u"Documentos", ondelete="cascade",
                                         help=u"Documentos de um Discente", invisible=True),
    }

    _defaults = {
        "ano": datetime.today().year,
    }

    def valida_fequencia(self, cr, uid, ids, context=None):
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

    _constraints = [
        (valida_fequencia, u"Não é possível criar novas frequências para meses que possuam outros registros em análise ou aceitos.", [u"Mês"]),
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
        return self.write(cr, uid, ids, {"state": "aceito"}, context)

    def botao_rejeitar(self, cr, uid, ids, context=None):
        """
        Altera o status para "rejeitado".
        """
        return self.write(cr, uid, ids, {"state": "rejeitado"}, context)
