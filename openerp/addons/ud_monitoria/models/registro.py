# coding: utf-8
from datetime import datetime, timedelta
from re import compile

from openerp import SUPERUSER_ID
from openerp.osv import fields, osv


class Registro(osv.Model):
    _name = "ud.monitoria.registro"
    _description = u"Modelo de configuração e registro de semestre (UD)"
    _order = "is_active desc, semestre desc"
    
    _campos_certificado = [
        (0, False, {"name": "discente", "descricao": u"Nome completo do discente"}),
        (0, False, {"name": "is_bolsista", "descricao": u"Booleano informando se é bolsista ou não"}),
        (0, False, {"name": "is_tutor", "descricao": u"Booleano informando se participou como tutor"}),
        (0, False, {"name": "curso", "descricao": u"Nome do curso"}),
        (0, False, {"name": "turno", "descricao": u"Turno do curso"}),
        (0, False, {"name": "modalidade", "descricao": u"Informa se o curso é bacharelado ou licenciatura"}),
        (0, False, {"name": "campus", "descricao": u"Nome do Campus do curso"}),
        (0, False, {"name": "disciplinas", "descricao": u"Lista com o nome das disciplinas participantes"}),
        (0, False, {"name": "orientador", "descricao": u"Nome completo do Orientador"}),
        (0, False, {"name": "carga_horaria", "descricao": u"Carga horária total de monitoria"}),
        (0, False, {"name": "data", "descricao": u"Data atual no formato \"DIA de MÊS de ANO\".\n"\
                                                 u"Ex.: 13 de Abril de 2016\n\n"\
                                                 u"Obs: Os campos numéricos \"dia\", \"mes\" e \"ano\" também estarão disponíveis."}),
        (0, False, {"name": "periodo_inicial", "descricao": u"Data que o discente iniciou as atividades de monitoria/tutoria "\
                                                            u"no formato DIA/MES/ANO."}),
        (0, False, {"name": "periodo_final", "descricao": u"Data que o discente finalizou as atividades de monitoria/tutoria "\
                                                         u"no formato DIA/MES/ANO."}),
    ]
    _campos_relatorio = [
        (0, False, {"name": "discente", "descricao": u"Nome completo do discente"}),
        (0, False, {"name": "relatorio", "descricao": u"Booleano que verifica se o relatório do discente está foi entregue e aprovado"}),
        (0, False, {"name": "meses_frequencia", "descricao": u"Dicionário que informa se as frequências mensais dos meses estão todas em ordem.\nObs.: {'num_mes': booleano}"}),
    ]
    
    def valida_intervalo_frequencia(self, cr, uid, ids, context=None):
        for registro in self.browse(cr, uid, ids, context=context):
            if (registro.intervalo_frequencia < 1):
                return False
        return True

    def valida_semestre(self, cr, uid, ids, context=None):
        padrao = compile("\d{4}\.[12]")
        for registro in self.browse(cr, uid, ids, context=context):
            if not padrao.match(registro.semestre):
                return False
        return True

    def valida_bolsas(self, cr, uid, ids, context=None):
        for reg in self.browse(cr, uid, ids, context):
            bolsas = 0
            for dist in reg.distribuicao_bolsas_ids:
                bolsas += dist.bolsas
            if bolsas > reg.max_bolsas:
                return False
        return True

    def __get_create(self, cr, nome, campos, template=u"Template não definido pelo administrador.", context=None):
        tipo_doc_model = self.pool.get("ud.documento.tipo")
        tipos_doc = tipo_doc_model.search(cr, SUPERUSER_ID, [("name", "=", nome)], context=context)
        if tipos_doc:
            return tipos_doc[0]
        return tipo_doc_model.create(cr, SUPERUSER_ID, {"name": nome, "modulo_externo": True, "campos_ids": campos, "template": template,
                                                        "info": u"ATENÇÃO: Não modifique o nome do tipo e tenha cuidado com alterações nos campos, "\
                                                                u"pois esses são usados internamente pelo módulo de monitoria.",})
    
    def __modelo_certificado(self, cr, uid, context=None):
        return self.__get_create(cr, u"CERTIFICADO (UD MONITORIA)", self._campos_certificado, context=context)
    
    def __modelo_relatorio_final(self, cr, uid, context=None):
        return self.__get_create(cr, u"RELATÓRIO FINAL (UD MONITORIA)", self._campos_relatorio, context=context)

    def getl_bolsas_distribuidas(self, cr, uid, ids, campo, args, context=None):
        res = {}
        for registro in self.browse(cr, uid, ids, context):
            res[registro.id] = 0
            for dist in registro.distribuicao_bolsas_ids:
                res[registro.id] = dist.bolsas

        return res

    _columns = {
        "id": fields.integer(u"ID", readonly=True, invisible=True),
        "semestre": fields.char(u"Semestre", size=6, required=True, help=u"Semestre no formato '2016.1'"),
        "max_bolsas": fields.integer(u"Máximo de Bolsas", required=True,
                                     help=u"Número máximo de bolsas disponíveis para o semestre"),
        "bolsas_distribuidas": fields.function(getl_bolsas_distribuidas, type="integer", string=u"Bolsas Distribuidas", help=u"Número total de bolsas distribuidas entre os cursos"),
        "distribuicao_bolsas_ids": fields.one2many("ud.monitoria.distribuicao.bolsas", "registro_id", u"Distribuição de Bolsas",
                                                   help=u"Permite distribuir bolsas entre cursos ativos"),
        "data_i_frequencia": fields.date(u"Envio de Frequência", required=True,
                                         help=u"Próxima data para submissão da frequências"),
        "intervalo_frequencia": fields.integer(u"Período (Dias)", required=True, help=u"Intervalo de submissão de frequências"),
        "processos_seletivos_ids": fields.one2many("ud.monitoria.processo.seletivo", "semestre_id", u"Processos Seletivos"),
        "modelo_certificado_id": fields.many2one("ud.documento.tipo", u"Modelo de Certificado", required=True,
                                                 readonly=True, ondelete="restrict", help=u"Modelo de certificado"),
        "modelo_relatorio_id": fields.many2one("ud.documento.tipo", u"Modelo de relatório", required=True, readonly=True,
                                               ondelete="restrict", help=u"Modelo do relatório final individual dos discentes"),
        "relatorio_discentes_ids": fields.one2many("ud.monitoria.relatorio.final.disc", "registro_id", u"Relatórios Finais", readonly=True,
                                                   help=u"Status de entrega de documentos e frequências dos discentes"),
        "eventos_ids": fields.one2many("ud.monitoria.evento", "registro_id", u"Eventos Ocorridos",
                                              help=u"Registro de eventos em Geral ocorridos durante o semestre"),
        "is_active": fields.boolean(u"Ativo", readonly=True),
    }

    _rec_name = "semestre"

    _constraints = [
        (valida_intervalo_frequencia, u"O intervalo da frequência deve ser maior que 0.", [u"Período da frequência"]),
        (valida_semestre, u"Semestre inválido.", [u"Semestre"]),
        (valida_bolsas, u"Número máximo de Bolsas excedido.", [u"Distribuição de Bolsas"]),
    ]
    
    _sql_constraints = [
        ("semestre_registro_uniq", "unique (semestre)", u"Não é permitido criar registros com semestres iguais!"),
    ]
    
    _defaults = {
        "intervalo_frequencia": 10,
        "is_active": True,
        "modelo_certificado_id": __modelo_certificado,
        "modelo_relatorio_id": __modelo_relatorio_final,
        "data_i_frequencia": (datetime.now() + timedelta(30)).strftime("%Y-%m-%d"),
    }

    def copy(self, cr, uid, id, default=None, context=None):
        default = default or {}
        def proximo_semestre(s):
            if s:
                ano, s = map(int, s.split("."))
                if s == 1:
                    s += 1
                else:
                    ano += 1
                    s = 1
                if self.search_count(cr, uid, [("semestre", "=", "%d.%d" % (ano, s))], context=context) > 0:
                    return proximo_semestre("%d.%d" % (ano, s))
                return "%d.%d" % (ano, s)
            return s

        semestre = default.get("semestre", False)
        if not semestre:
            hoje = datetime.today()
            semestre = "%d.%d" % (hoje.year, 1 if hoje.month <= 6 else 2)
        default.update({
            "semestre": proximo_semestre(semestre),
            "data_i_frequencia": (datetime.now() + timedelta(30)).strftime("%Y-%m-%d"),
            "processos_seletivos_ids": [],
            "relatorio_discentes_ids": [],
            "evento_ids": [],
            "is_active": True
        })
        return super(Registro, self).copy(cr, uid, id, default, context)

    def atualizar_datas_frequencia(self, cr, uid, context=None):
        return []
    
    def ativar_registro(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {"is_active": True}, context=context)
    
    def desativar_registro(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {"is_active": False}, context=context)
    
    def resetar_modelos(self, cr, uid, ids, context=None):
        """
        Restaura os campos e as informações adicionais padrão dos modelos de certificado e relatório final.
        """
        tipo_doc_model = self.pool.get("ud.documento.tipo")
        for modelos in self.read(cr, uid, ids, ["modelo_certificado_id", "modelo_relatorio_id"], context=context, load="_classic_write"):
            tipo_doc_model.botao_remover_campos(cr, uid, [modelos["modelo_certificado_id"]], context)
            tipo_doc_model.write(cr, uid, context=context)
            tipo_doc_model.botao_remover_campos(cr, uid, [modelos["modelo_relatorio_id"]], context)
            tipo_doc_model.write(cr, uid, context=context)
        return True


class DistribuicaoBolsas(osv.Model):
    _name = "ud.monitoria.distribuicao.bolsas"
    _description = u"Distribuição de bolsas de cursos (UD)"

    def get_bolsas_distribuidas(self, cr, uid, ids, campo, args, context=None):
        res = {}.fromkeys(ids, 0)
        processo_seletivo_model = self.pool.get("ud.monitoria.processo.seletivo")
        disciplina_model = self.pool.get("ud.monitoria.disciplina")
        for distribuicao in self.browse(cr, uid, ids, context):
            processos_seletivos = processo_seletivo_model.search(cr, uid, [("semestre_id", "=", distribuicao.registro_id.id)], context=context)
            disciplinas = disciplina_model.search(cr, uid, [("curso_id", "=", distribuicao.curso_id.id), ("processo_seletivo_id", "in", processos_seletivos)], context=context)
            for disciplina in disciplina_model.browse(cr, uid, disciplinas, context):
                res[distribuicao.id] += disciplina.bolsas
        return res

    def update_bolsas_distribuidas(self, cr, uid, ids, context=None):
        res = []
        for disciplina in self.browse(cr, uid, ids, context):
            res.extend([dist.id for dist in disciplina.processo_seletivo_id.semestre_id.distribuicao_bolsas_ids])
        return res

    _columns = {
        "id": fields.integer("ID", readonly=True, invisible=True),
        "curso_id": fields.many2one("ud.curso", u"Curso", required=True, ondelete="restrict",
                                    domain=[("is_active", "=", True)]),
        "is_active": fields.related("curso_id", "is_active", type="boolean", string=u"Curso Ativo?", readonly=True,
                                    help=u"Identifica se atualmente o curso está ativo ou não"),
        "bolsas": fields.integer(u"Bolsas", required=True, help=u"Número de bolsas disponibilizadas para o curso"),
        "bolsas_distribuidas": fields.function(get_bolsas_distribuidas, type="integer", string=u"Bolsas Distribuídas",
                                               store={"ud.monitoria.disciplina": (update_bolsas_distribuidas, ["bolsas"], 10)},
                                               help=u"Número de bolsas distribuídas entre as disciplinas ativas e não ativas do curso"),
        "registro_id": fields.many2one("ud.monitoria.registro", u"Registro", ondelete="cascade"),
    }

    _sql_constraints = [
        ("distribuicao_d_registro_uniques", "unique(curso_id,registro_id)",
         u"Não é permitido distribuir bolsas de cursos repetidos em um mesmo registro semestral."),
    ]


class Evento(osv.Model):
    _name = "ud.monitoria.evento"
    _description = u"Registro geral de eventos ocorridos no semestre (UD)"
    _order = "state asc,create_date asc"
    
    def responsavel(self, cr, uid, context=None):
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

    def valida_registro(self, cr, uid, ids, context=None):
        for registro in self.browse(cr, uid, ids, context=context):
            if not registro.registro_id.is_active:
                return False
        return True
    
    _STATES = [
        ("novo", u"Novo"),
        ("visto", u"Visualizado"),
    ]
    
    _columns = {
        "responsavel_id": fields.many2one("ud.employee", u"Responsável", required=True, readonly=True,
                                          ondelete="restrict", help=u"Pessoa que ocasionou o evento"),
        "create_date": fields.datetime(u"Data do evento", readonly=True),
        "name": fields.char(u"Nome", required=True),
        "envolvidos_ids": fields.many2many("ud.employee", "ud_monitoria_envolvidos_evento", "evento_id", "pessoa_id",
                                           u"Envolvidos", ondelete="restrict"),
        "descricao": fields.text(u"Descrição"),
        "registro_id": fields.many2one("ud.monitoria.registro", u"Registro", required=True, ondelete="cascade"),
        "state": fields.selection(_STATES, u"Status", readonly=True),
    }
    
    _defaults = {
        "state": "novo",
        "responsavel_id": responsavel,
    }
    
    _constraints = [
        (valida_registro, u"O Registro não está mais ativo!", [u"Registro"])
    ]
    
    def botao_visualizar(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {"state": "visto"}, context=context)


class RelatorioFinalDisc(osv.Model):
    _name = "ud.monitoria.relatorio.final.disc"
    _description = u"Relatório de status final dos discentes (UD)"
    _order = "doc_discente_id"
    
    def valida_registro(self, cr, uid, ids, context=None):
        for registro in self.browse(cr, uid, ids, context=context):
            if not registro.registro_id.is_active:
                return False
        return True

    def relatorio(self, cr, uid, ids, campos, args, context=None):
        res = {}
        for rel_f in self.browse(cr, uid, ids, context):
            res[rel_f.id] = rel_f.doc_discente_id.relatorios_ok
        return res

    def update_relatorio(self, cr, uid, ids, context=None):
        rel_model, self = self, self.pool.get("ud.monitoria.relatorio.final.disc")
        doc_disc = []
        if self._name == "ud.monitoria.relatorio":
            for rel in rel_model.browse(cr, SUPERUSER_ID, ids, context):
                doc_disc.append(rel.documentos_id.id)
        elif self._name == "ud.monitoria.documentos.discente":
            doc_disc = ids
        return self.search(cr, uid, [("doc_discente_id", "in", doc_disc)], context=context)

    _STATES = [
        ("reserva", u"Cadastro de Reserva"),
        ("n_bolsista", u"Não Bolsista"),
        ("bolsista", u"Bolsista"),
        ("desligado", u"Desligado(a)"),
    ]

    _columns = {
        "write_date": fields.datetime(u"Última atualização", readonly=True),
        "doc_discente_id": fields.many2one("ud.monitoria.documentos.discente", u"Discente", required=True, ondelete="cascade"),
        "disciplina_id": fields.related("doc_discente_id", "disciplina_id", type="many2one", readonly=True,
                                         relation="ud.monitoria.disciplina", string=u"Disciplinas"),
        "state": fields.related("doc_discente_id", "state", type="selection", readonly=True, selection=_STATES,
                                string=u"Status"),
        "is_active": fields.related("doc_discente_id", "is_active", type="boolean", string=u"Ativo?", readonly=True),
        "relatorio": fields.function(relatorio, type="boolean", string=u"Relatório?",
                                     help=u"Informa se o discente entregou o relatório corretamente",
                                     store={
                                         "ud.monitoria.relatorio": (update_relatorio, ["state"], 10),
                                         "ud.monitoria.documentos.discente": (update_relatorio, ["relatorio_ids"], 10),
                                     }),
        "meses_frequencia_ids": fields.one2many("ud.monitoria.rfd.mes", "relatorio_id", u"Frequências?",
                                                help=u"Informa quais meses o discente precisa(ou) anexar sua frequência e qual é seu status"),
        "registro_id": fields.many2one("ud.monitoria.registro", u"Registro", required=True, ondelete="cascade", invisible=True),
    }
    
    _constraints = [
        (valida_registro, u"O registro semestral não está mais ativo!", [u"Registro/Semestre"])
    ]

    _sql_constraints = [
        ("relatorio_doc_discent_unico", "unique(doc_discente_id)",
         u"Os documentos de um discente não pode conter mais de um relatório"),
    ]

    def create(self, cr, uid, vals, context=None):
        if vals.get("doc_discente_id", False):
            doc = self.pool.get("ud.monitoria.documentos.discente").browse(cr, uid, vals["doc_discente_id"], context)
            if "registro_id" not in vals:
                vals["registro_id"] = doc.disciplina_id.semestre_id.id
            vals["meses_frequencia_ids"] = []
            meses = []
            for freq in doc.frequencia_ids:
                if freq.mes not in meses:
                    vals["meses_frequencia_ids"].append((0, 0, {"mes": freq.mes}))
                    meses.append(freq.mes)
        return super(RelatorioFinalDisc, self).create(cr, uid, vals, context)

    # def add_meses(self, cr, uid, ids, meses, context=None):
    #     meses = set(meses)
    #     for rel in self.browse(cr, uid, ids, context):
    #         exist = set()
    #         for fm in rel.meses_frequencia_ids:
    #             exist.add(fm.mes)
    #         add = []
    #         for mes in meses.difference(exist):
    #             add.append((0, 0, {"mes": mes}))
    #         if add:
    #             rel.write({"meses_frequencia_ids": add})


class RelatorioFimDiscMes(osv.Model):
    _name = "ud.monitoria.rfd.mes"
    _description = u"Controle da frequência mensal dos discentes (UD)"
    _order = "mes asc"
    
    def get_mes(self, cr, uid, ids, campo, arg, context=None):
        res = {}
        meses = {'01': u"Janeiro", '02': u"Fevereiro", '03': u"Março", '04': u"Abril", '05': u"Maio", '06': u"Junho",
                 '07': u"Julho", '08': u"Agosto", '09': u"Setembro", '10': u"Outubro", '11': u"Novembro", '12': u"Dezembro"}
        for mes in self.read(cr, uid, ids, ["seq"], context=context, load="_classic_write"):
            res[mes.get("id")] = meses.get(mes.get("seq"))
        return res

    def get_status(self, cr, uid, ids, campo, arg, context=None):
        res = {}
        for mes in self.browse(cr, uid, ids, context):
            res[mes.id] = "s_registro"
            for freq in mes.relatorio_id.doc_discente_id.frequencia_ids:
                if freq.mes == mes.mes:
                    if freq.state == "aceito":
                        res[mes.id] = "regular"
                        break
                    elif freq.state == "analise":
                        res[mes.id] = "analise"
                    elif res[mes.id] == "s_registro" and freq.state == "rejeitado":
                        res[mes.id] = "rejeitado"
        return res

    _MESES = [('01', u"Janeiro"), ('02', u"Fevereiro"), ('03', u"Março"), ('04', u"Abril"), ('05', u"Maio"),
              ('06', u"Junho"), ('07', u"Julho"), ('08', u"Agosto"), ('09', u"Setembro"), ('10', u"Outubro"),
              ('11', u"Novembro"), ('12', u"Dezembro")]

    _STATES = [("s_registro", u"Sem Registro"), ("rejeitado", u"Rejeitado"), ("analise", u"Análise"), ("regular", u"Regular")]

    _columns = {
        "name": fields.function(get_mes, type="char", store=False, method=True, string=u"Nome do Mês"),
        "mes": fields.selection(_MESES, u"Mês", required=True),
        "state": fields.function(get_status, type="selection", selection=_STATES, string=u"Status",
                                 help=u"Seguindo a ordem de prioridade, se houver ao menos uma frequência em análise, "
                                      u"o status será \"Análise\", se houver alguma aceita, o status passa a ser "
                                      u"\"Regular\""),
        "relatorio_id": fields.many2one("ud.monitoria.relatorio.final.disc", u"Relatório Final", ondelete="cascade",
                                        invisible=True),
    }
    
    _sql_constraints = [
        ("mes_relatorio_unique", "unique(mes, relatorio_id)", u"Não é permitido repetir o mês para o mesmo relatório!"),
    ]
