#coding: utf-8

from openerp import SUPERUSER_ID
from openerp.osv import fields, osv
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

from datetime import datetime
from pytz import timezone
from re import compile


def localise(data, tz):
    return timezone(tz).localize(data, is_dst=False)

def datetime_to_utc(data, tz):
    try:
        data = datetime.strptime(data, DEFAULT_SERVER_DATETIME_FORMAT)
    except ValueError:
        data = datetime.strptime(data, DEFAULT_SERVER_DATE_FORMAT)
    return localise(data, tz).astimezone(timezone("UTC"))


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
    
    def valida_data_frequencia(self, cr, uid, ids, context=None):
        tz = (context or {}).get("tz", "America/Maceio")
        hoje = localise(datetime.utcnow(), "UTC").date()
        for registro in self.browse(cr, uid, ids, context=context):
            create_date = datetime_to_utc(registro.create_date, tz).date()
            data_freq = datetime_to_utc(registro.data_i_frequencia, tz).date()
            if data_freq <= create_date and hoje >= data_freq:
                return False
        return True
    
    def valida_intervalo_frequencia(self, cr, uid, ids, context=None):
        for registro in self.browse(cr, uid, ids, context=context):
            if (registro.intervalo_frequencia < 1):
                return False
        return True
    
    def valida_vagas(self, cr, uid, ids, context=None):
        for registro in self.browse(cr, uid, ids, context=context):
            if registro.vagas_bolsistas < 0:
                return False
        return True
    
    def valida_semestre(self, cr, uid, ids, context=None):
        padrao = compile("\d{4}\.[12]")
        for registro in self.browse(cr, uid, ids, context=context):
            if not padrao.match(registro.semestre):
                return False
        return True

    def valida_media_minima(self, cr, uid, ids, context=None):
        for registro in self.browse(cr, uid, ids, context=context):
            if registro.media_minima <= 0:
                return False
        return True

    def calcular_bolsas(self, cr, uid, context=None):
        oferta_model = self.pool.get("ud.monitoria.oferta.disciplina")
        ofertas_ids = oferta_model.search(cr, uid, [("em_oferta", "=", True)], context=context)
        vagas = 0
        for oferta in oferta_model.read(cr, uid, ofertas_ids, ["bolsas_disponiveis"], context=context):
            vagas += oferta.get("bolsas_disponiveis")
        return vagas
    
    def _num_bolsas(self, cr, uid, ids, campo, args, context=None):
        return {}.fromkeys(ids, self.calcular_bolsas(cr, uid, context))
    
    def _update_bolsas(self, cr, uid, ids, context=None):
        return self.pool.get("ud.monitoria.registro").search(cr, uid, [("is_active", "=", True)], context=context)
    
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
    
    _columns = {
        "id": fields.integer(u"ID", readonly=True, invisible=True),
        "create_date": fields.datetime(u"Data de Criação", readonly=True, invisible=True),
        "semestre": fields.char(u"Semestre", size=6, required=True, help=u"Semestre no formato '2016.1'"),
        "vagas_bolsistas": fields.function(_num_bolsas, type="integer", method=True, string=u"Bolsas Disponíveis",
                                           required=True, store={
                                               "ud.monitoria.registro": (_update_bolsas, ["is_active"], 10),
                                                "ud.monitoria.oferta.disciplina": (_update_bolsas, ["em_oferta", "bolsas_disponiveis"], 10)
                                           }, help=u"Informa a quantidade de bolsas atualmente disponívels"),
        "data_i_frequencia": fields.date(u"Envio de Frequência", required=True,
                                         help=u"Próxima data para submissão da frequências"),
        "intervalo_frequencia": fields.integer(u"Período (Dias)", required=True, help=u"Intervalo de submissão de frequências"),
        "modelo_certificado_id": fields.many2one("ud.documento.tipo", u"Modelo de Certificado", required=True,
                                                 readonly=True, ondelete="restrict", help=u"Modelo de certificado"),
        "modelo_relatorio_id": fields.many2one("ud.documento.tipo", u"Modelo de relatório", required=True, readonly=True,
                                               ondelete="restrict", help=u"Modelo do relatório final individual dos discentes"),
        "relatorio_discentes_ids": fields.one2many("ud.monitoria.relatorio.final.disc", "registro_id", u"Relatórios Finais", readonly=True,
                                                   help=u"Status de entrega de documentos e frequências dos discentes"),
        "demanda_ids": fields.one2many("ud.monitoria.solicitacao", "semestre_id", u"Demanda de disciplinas", readonly=True,
                                       help=u"Demanda de disciplinas para o semestre do registro"),
        "desligamentos_ids": fields.one2many("ud.monitoria.desligamento", "registro_id", u"Solicitações de Desligamento", readonly=True,
                                             help=u"Permite gerenciar as solicitações de desligamento"),
        "outros_eventos_ids": fields.one2many("ud.monitoria.evento", "registro_id", u"Eventos Ocorridos",
                                              help=u"Registro de eventos em Geral ocorridos durante o semestre"),
        "is_active": fields.boolean(u"Ativo", readonly=True),
        "media_minima": fields.float(u"Nota Minima", required=True, help=u"Média mínima para aprovação de discentes."),
        "tipo_media": fields.selection([("a", u"Aritmética"), ("p", u"Ponderada")], u"Tipo de Média", required=True,
                                       help=u"Tipo de média a ser utilizada na aprovação."),
    }
    
    _rec_name = "semestre"
    
    _constraints = [
        (valida_data_frequencia, u"A data da frequência deve ocorrer após a data atual", [u"Data da Frequência"]),
        (valida_intervalo_frequencia, u"O intervalo da frequência deve ser maior que 0.", [u"Período da frequência"]),
        (valida_vagas, u"O número de vagas para bolsistas não pode ser negativo", [u"Vagas de Bolsistas"]),
        (valida_semestre, u"Semestre inválido", [u"Semestre"]),
        (valida_media_minima, u"Não é permitido nota menor ou igual a 0.", [u"Nota Mínima"])
    ]
    
    _sql_constraints = [
        ("semestre_registro_uniq", "unique (semestre)", u"Não é permitido criar registros com semestres iguais!"),
    ]
    
    _defaults = {
        "intervalo_frequencia": 10,
        "is_active": True,
        "modelo_certificado_id": __modelo_certificado,
        "modelo_relatorio_id": __modelo_relatorio_final,
        "vagas_bolsistas": calcular_bolsas,
        "media_minima": 7.0,
        "tipo_media": "p",
    }
    
    def unlink(self, cr, uid, ids, context=None):
        solic_ids = []
        for reg in self.read(cr, uid, ids, ["demanda_ids"], context=context):
            solic_ids += reg["demanda_ids"]
        self.pool.get("ud.monitoria.solicitacao").unlink(cr, uid, solic_ids, context=context)
        return super(Registro, self).unlink(cr, uid, ids, context=context)
    
    def atualizar_datas_frequencia(self, cr, uid, context=None):
        return []
    
    def botao_ativar_registro(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {"is_active": True}, context=context)
    
    def botao_desativar_registro(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {"is_active": False}, context=context)
    
    def botao_resetar_modelos(self, cr, uid, ids, context=None):
        """
        Restaura os campos e as informações adicionais padrão dos modelos de certificado e relatório final.
        """
        tipo_doc_model = self.pool.get("ud.documento.tipo")
        for modelos in self.read(cr, uid, ids, ["modelo_certificado_id", "modelo_relatorio_id"], context=context, load="_classic_write"):
            tipo_doc_model.botao_remover_campos(cr, uid, [modelos["modelo_certificado_id"]], context)
            tipo_doc_model.write(cr, uid, modelos["modelo_certificado_id"], {"campos_ids": self._campos_certificado,
                                                                             "info": u"ATENÇÃO: Não modifique o nome do tipo e tenha cuidado "\
                                                                                     u"com alterações nos campos, pois esses "\
                                                                                     u"são usados internamente pelo módulo de monitoria."}, context=context)
            tipo_doc_model.botao_remover_campos(cr, uid, [modelos["modelo_relatorio_id"]], context)
            tipo_doc_model.write(cr, uid, modelos["modelo_relatorio_id"], {"campos_ids": self._campos_relatorio,
                                                                           "info": u"ATENÇÃO: Não modifique o nome do tipo e tenha cuidado "\
                                                                                   u"com alterações nos campos, pois esses "\
                                                                                   u"são usados internamente pelo módulo de monitoria."}, context=context)
        return True


class Evento(osv.Model):
    _name = "ud.monitoria.evento"
    _description = u"Registro geral de eventos ocorridos no semestre (UD)"
    _order = "state asc,create_date asc"
    
    def responsavel(self, cr, uid, context=None):
        ud_usuario_id = self.pool.get("ud.employee").search(cr, SUPERUSER_ID, [("user_id", "=", uid)], limit=2)
        ud_usuario_id = ud_usuario_id or []
        if len(ud_usuario_id) == 1:
            return ud_usuario_id[0]
        return False
    
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
        "responsavel_id": fields.many2one("ud.employee", u"Responsável", required=True, readonly=True, ondelete="restrict", help=u"Pessoa que foi principal responsável pelo evento"),
        "create_date": fields.datetime(u"Data do evento", readonly=True),
        "name": fields.char(u"Nome", required=True),
        "envolvidos_ids": fields.many2many("ud.employee", "ud_monitoria_envolvidos_evento", "evento_id", "pessoa_id", u"Envolvidos", ondelete="restrict"),
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
    _order = "is_active"
    
    def valida_registro(self, cr, uid, ids, context=None):
        for registro in self.browse(cr, uid, ids, context=context):
            if not registro.registro_id.is_active:
                return False
        return True

    def relatorio(self, cr, uid, ids, campos, args, context=None):
        res = {}
        for rel_f in self.browse(cr, uid, ids, context):
            res[rel_f.id] = {}
            if "relatorio" in campos:
                res[rel_f.id]["relatorio"] = rel_f.doc_discente_id.relatorios_ok
            if "is_active" in campos:
                res[rel_f.id]["is_active"] = not all(
                    [rel_f.doc_discente_id.relatorios_ok] +
                    [mf.regular for mf in rel_f.meses_frequencia_ids]
                )
        return res

    def update_relatorio(self, cr, uid, ids, context=None):
        rel_model, self = self, self.pool.get("ud.monitoria.relatorio.final.disc")
        rels = rel_model.search(cr, SUPERUSER_ID, [("state", "=", "aceito"), ("id", "in", ids)], context=context)
        doc_disc = []
        for rel in rel_model.browse(cr, SUPERUSER_ID, rels, context):
            doc_disc.append(rel.documentos_id.id)
        return self.search(cr, SUPERUSER_ID, [("doc_discente_id", "in", doc_disc)], context=context)

    def update_is_active(self, cr, uid, ids, context=None):
        return [fm.relatorio_id.id for fm in self.browse(cr, SUPERUSER_ID, ids, context)]

    _columns = {
        "doc_discente_id": fields.many2one("ud.monitoria.documentos.discente", u"Documentos do Discente", required=True, ondelete="cascade"),
        "discente_id": fields.related("doc_discente_id", "discente_id", string=u"Discente", readonly=True,
                                      type="many2one", relation="ud.monitoria.discente"),
        "relatorio": fields.function(relatorio, type="boolean", multi="_relatorio", string=u"Entrega do relatório",
                                     help=u"Informa se o discente entregou o relatório corretamente",
                                     store={"ud.monitoria.relatorio": (update_relatorio, ["state"], 10)}),
        "is_active": fields.function(relatorio, type="boolean", multi="_relatorio", string=u"Ativo?",
                                     store={"ud.monitoria.rfd.mes": (update_is_active, ["regular"], 10)}),
        # "relatorio": fields.boolean(u"Entrega do relatório", help=u"Informa se o discente entregou o relatório corretamente"),
        # "is_active": fields.boolean(u"Ativo"),
        "meses_frequencia_ids": fields.one2many("ud.monitoria.rfd.mes", "relatorio_id", u"Entrega das frequências",
                                                help=u"Informa quais meses o discente precisa(ou) anexar sua frequência e qual é seu status"),
        "write_date": fields.datetime(u"Última atualização", readonly=True),
        "registro_id": fields.many2one("ud.monitoria.registro", u"Registro", required=True, ondelete="cascade", invisible=True),
    }
    
    _defaults = {
        "is_active": True,
    }
    
    _constraints = [
        (valida_registro, u"O Registro não está mais ativo!", [u"Registro"])
    ]

    _sql_constraints = [
        ("relatorio_doc_discent_unico", "unique(doc_discente_id)",
         u"Os documentos de um discente não pode conter mais de um relatório"),
    ]

    def create(self, cr, uid, vals, context=None):
        if "doc_discente_id" in vals:
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

    def add_meses(self, cr, uid, ids, meses, context=None):
        meses = set(meses)
        for rel in self.browse(cr, uid, ids, context):
            exist = set()
            for fm in rel.meses_frequencia_ids:
                exist.add(fm.mes)
            add = []
            for mes in meses.difference(exist):
                add.append((0, 0, {"mes": mes}))
            if add:
                rel.write({"meses_frequencia_ids": add})


class RelatorioFimDiscMes(osv.Model):
    _name = "ud.monitoria.rfd.mes"
    _description = u"Controle da frequência mensal dos discentes (UD)"
    _order = "regular asc,mes asc"
    
    def get_mes(self, cr, uid, ids, campo, arg, context=None):
        res = {}
        meses = {'01': u"Janeiro", '02': u"Fevereiro", '03': u"Março", '04': u"Abril", '05': u"Maio", '06': u"Junho",
                 '07': u"Julho", '08': u"Agosto", '09': u"Setembro", '10': u"Outubro", '11': u"Novembro", '12': u"Dezembro"}
        for mes in self.read(cr, uid, ids, ["seq"], context=context, load="_classic_write"):
            res[mes.get("id")] = meses.get(mes.get("seq"))
        return res

    def frequencia_regular(self, cr, uid, ids, campo, arg, context=None):
        res = {}.fromkeys(ids, False)
        for mes in self.browse(cr, uid, ids, context):
            for freq in mes.relatorio_id.doc_discente_id.frequencia_ids:
                if freq.state == "aceito":
                    res[mes.id] = True
                    break
        return res

    def update_regular(self, cr, uid, ids, context=None):
        freq_model, rel_fim_model = self, self.pool.get("ud.monitoria.relatorio.final.disc")
        doc_disc = []
        meses = set()
        for freq in freq_model.browse(cr, SUPERUSER_ID, ids, context):
            doc_disc.append(freq.documentos_id.id)
            meses.add(freq.mes)
        rel_fim = rel_fim_model.search(cr, SUPERUSER_ID, [("doc_discente_id", "in", doc_disc)], context=context)
        res = []
        for rel_fim in rel_fim_model.browse(cr, SUPERUSER_ID, rel_fim, context):
            res += [mf.id for mf in rel_fim.meses_frequencia_ids if mf.mes in meses]
        return res

    _MESES = [('01', u"Janeiro"), ('02', u"Fevereiro"), ('03', u"Março"), ('04', u"Abril"), ('05', u"Maio"),
              ('06', u"Junho"), ('07', u"Julho"), ('08', u"Agosto"), ('09', u"Setembro"), ('10', u"Outubro"),
              ('11', u"Novembro"), ('12', u"Dezembro")]
    
    _columns = {
        "name": fields.function(get_mes, type="char", store=False, method=True, string=u"Nome do Mês"),
        "mes": fields.selection(_MESES, u"Mês", required=True),
        "regular": fields.function(frequencia_regular, type="boolean", string=u"Regular?",
                                    help=u"Infora se a frequência do mês específico está regular.",
                                   store={"ud.monitoria.frequencia": (update_regular, ["state"], 10)}),
        # "regular": fields.boolean(u"Regular?", help=u"Infora se a frequência do mês específico está regular."),
        "relatorio_id": fields.many2one("ud.monitoria.relatorio.final.disc", u"Relatório Final", ondelete="cascade",
                                        invisible=True),
    }
    
    _sql_constraints = [
        ("mes_relatorio_unique", "unique(mes, relatorio_id)", u"Não é permitido repetir o mês para o mesmo relatório!"),
    ]


class Desligamento(osv.Model):
    _name = "ud.monitoria.desligamento"
    _description = u"Info: desligamento de discentes (UD)"
    _order = "state desc"
    
    def valida_registro(self, cr, uid, ids, context=None):
        for registro in self.browse(cr, uid, ids, context=context):
            if not registro.registro_id.is_active:
                return False
        return True
    
    _STATES = [
        ("novo", u"Novo"),
        ("confirmado", u"Confirmado"),
    ]
    
    _columns = {
        # "orientador_solicitante_id": fields.many2one("ud.monitoria.orientador", u"Orientador", required=True, ondelete="restrict"),
        # "discente_id": fields.many2one("ud.monitoria.discente", u"Discente", required=True, ondelete="restrict"),
        "disciplina_id": fields.many2one("ud.disciplina", u"Disciplina", required=True, ondelete="restrict"),
        "justificativa": fields.text(u"Justificativa", required=True),
        "info_adicionais": fields.text(u"Informações adicionais"),
        "state": fields.selection(_STATES, u"Status", readonly=True),
        "registro_id": fields.many2one("ud.monitoria.registro", u"Registro", required=True, invisible=False, ondelete="cascade"),
    }
    
    _constraints = [
        (valida_registro, u"O Registro não está mais ativo!", [u"Registro"])
    ]
    
    def create(self, cr, user, vals, context=None):
        vals["state"] = "novo"
        vals["info_adicionais"] = vals.get("info_adicionais", u"Nenhuma informação adicional") or u"Nenhuma informação adicional"
        return osv.osv.create(self, cr, user, vals, context=context)
    
    def botao_confirmar(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {"state": "confirmado"}, context=context)


class SolicitacaoDisciplina(osv.Model):
    _name = "ud.monitoria.solicitacao.disciplina"
    _description = u"Disciplina de solicitação para monitoria (UD)"
    _inherit = "ud.monitoria.info.disciplina"
    
    def bolsas_disponiveis(self, cr, uid, ids, campo, args, context=None):
        oferta_model = self.pool.get("ud.monitoria.oferta.disciplina")
        res = {}
        for disc in self.read(cr, uid, ids, ["curso_id", "disciplina_id"], context=context, load="_classic_write"):
            ofertas_ids = oferta_model.search(cr, uid, [
                ("curso_id", "=", disc["curso_id"]), ("disciplina_id", "=", disc["disciplina_id"])
            ], context=context)
            if ofertas_ids:
                res[disc["id"]] = oferta_model.read(cr, uid, ofertas_ids[0], ["bolsas_disponiveis"], context=context,
                                                    load="_classic_write")["bolsas_disponiveis"]
        return res
    
    def valida_vagas(self, cr, uid, ids, context=None):
        for disc in self.read(cr, uid, ids, ["monitor_s_bolsa", "tutor_s_bolsa"], context=context, load="_classic_write"):
            if disc["monitor_s_bolsa"] == 0 and disc["tutor_s_bolsa"] == 0 or (disc["monitor_s_bolsa"] < 0 or disc["tutor_s_bolsa"] < 0):
                return False
        return True
    
    def valida_datas(self, cr, uid, ids, context=None):
        for disc in self.browse(cr, uid, ids, context=context):
            if datetime.strptime(disc.data_inicial, DEFAULT_SERVER_DATE_FORMAT) > datetime.strptime(disc.data_final, DEFAULT_SERVER_DATE_FORMAT):
                return False
        return True
    
    _columns = {
        "monitor_s_bolsa": fields.integer(u"Vagas sem bolsa (Monitor)", required=True),
        "tutor_s_bolsa": fields.integer(u"Vagas sem bolsa (Tutor)", required=True),
        "num_bolsas": fields.function(bolsas_disponiveis, type="integer", string=u"Bolsas disponíveis"),
        "solicitacao_id": fields.many2one("ud.monitoria.solicitacao", u"Solicitação", ondelete="cascade", required=True, invisible=True),
    }
    
    _constraints = [
        (valida_vagas, u"O número de vagas não podem ser negativos ou com os 2 campos igual a 0.", [u"Vagas para monitor e tutor"]),
        (valida_datas, u"A data inicial não pode ocorrer depois da final", [u"Datas Inicial e Final"]),
    ]
    
    def name_get(self, cr, uid, ids, context=None):
        return [(disc.id, disc.disciplina_id.name) for disc in self.browse(cr, uid, ids, context=context)]
    
    def name_search(self, cr, uid, name='', args=None, operator='ilike', context=None, limit=100):
        if not isinstance(args, (list, tuple)):
            args = []
        if not (name == '' and operator == 'ilike'):
            disciplinas_ids = self.pool.get("ud.disciplina").search(cr, uid, [("name", operator, name)], context=context)
            args += [("disciplina_id", "in", disciplinas_ids)]
        ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)
    
    def ativar(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {"is_active": True})
    
    def desativar(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {"is_active": False})
    
    def onchange_siape(self, cr, uid, ids, siape, context=None):
        if siape:
            perfil_model = self.pool.get("ud.perfil")
            papel_id = perfil_model.search(cr, SUPERUSER_ID, [("matricula", "=", siape),
                                                              ("tipo", "=", "p")], context=context)
            if papel_id:
                return {"value": {"orientador_id": perfil_model.read(cr, SUPERUSER_ID, papel_id[0], ["ud_papel_id"], context=context).get("ud_papel_id")}}
        return {"value": {"orientador_id": False, "siape": False},
                "warning": {"title": u"Alerta", "message": u"SIAPE informado inexistente."}}
    
    def onchange_curso(self, cr, uid, ids, curso_id, context=None):
        if curso_id:
            oferta_model = self.pool.get("ud.monitoria.oferta.disciplina")
            ofertas_ids = oferta_model.search(cr, uid, [("curso_id", "=", curso_id), ("em_oferta", "=", True)], context=context)
            if ofertas_ids:
                disc_ids = [oferta["disciplina_id"] for oferta in oferta_model.read(cr, uid, ofertas_ids, ["disciplina_id"], context=context, load="_classic_write")]
                return {"value": {"disciplina_id": False},
                        "domain": {"disciplina_id": [('id', 'in', disc_ids)]}}
        return {"value": {"disciplina_id": False},
                "domain": {"disciplina_id": [('id', '=', [])]}}
    
    def onchange_disciplina(self, cr, uid, ids, curso_id, disciplina_id, context=None):
        if curso_id and disciplina_id:
            oferta_model = self.pool.get("ud.monitoria.oferta.disciplina")
            ofertas_ids = oferta_model.search(cr, uid, [("curso_id", "=", curso_id), ("disciplina_id", "=", disciplina_id)], context=context)
            if ofertas_ids:
                return {"value": {"num_bolsas": oferta_model.read(cr, uid, ofertas_ids[0], ["bolsas_disponiveis"], context=context, load="_classic_write")["bolsas_disponiveis"]}}
        return {"value": {"num_bolsas": 0}}


class Solicitacao(osv.Model):
    _name = "ud.monitoria.solicitacao"
    _description = u"Solicitação de disciplinas para monitoria (UD)"
    _order = "is_active desc,semestre_id desc"
    
    def get_ativo(self, cr, uid, ids, campo, args, context=None):
        res = {}
        for solicitacao in self.browse(cr, uid, ids, context=context):
            ativo = False
            for disc in solicitacao.disciplinas_ids:
                ativo = ativo or disc.is_active
            res[solicitacao.id] = ativo
        return res
    
    def atualiza_ativo(self, cr, uid, ids, context=None):
        return [disc.solicitacao_id.id for disc in self.browse(cr, uid, ids, context=context)]
    
    def solicitante(self, cr, uid, context=None):
        """
        Busca qual pessoa no núcleo está vinculada ao usuário atualmente logado.
        
        :param cr: Cursor do Banco de dados
        :param uid: ID do Usuário logado
        :type uid: Inteiro
         
        :return: Retorna o id de um registro de ud_employee ou False
        """
        ud_usuario_id = self.pool.get("ud.employee").search(cr, SUPERUSER_ID, [("user_id", "=", uid)], limit=2)
        ud_usuario_id = ud_usuario_id or []
        if len(ud_usuario_id) == 1:
            return ud_usuario_id[0]
        return False
    
    def valida_registro(self, cr, uid, ids, context=None):
        for solicitacao in self.browse(cr, uid, ids, context=context):
            if not solicitacao.semestre_id.is_active:
                return False
        return True
    
    def valida_disciplinas(self, cr, uid, ids, context=None):
        discs = []
        for solicitacao in self.browse(cr, uid, ids, context=context):
            for disc in solicitacao.disciplinas_ids:
                if disc.disciplina_id.id in discs:
                    return False
                else:
                    discs.append(disc.disciplina_id.id)
        return True
    
    _columns = {
        "solicitante_id": fields.many2one("ud.employee", u"Solicitante", required=True, readonly=True, ondelete="restrict"),
        "semestre_id": fields.many2one("ud.monitoria.registro", u"Semestre", required=True, ondelete="cascade",
                                       domain=[("is_active", "=", True)], help=u"Semestre ativos configurados no registro"),
        "disciplinas_ids": fields.one2many("ud.monitoria.solicitacao.disciplina", "solicitacao_id", u"Disciplinas"),
        "is_active": fields.function(get_ativo, type="boolean", string=u"Ativo", method=True,
                                     store={"ud.monitoria.solicitacao.disciplina": (atualiza_ativo, ["is_active"], 10)}),
    }
    
    _defaults = {
        "solicitante_id": solicitante,
        "is_active": True,
    }
    
    _constraints = [
        (valida_registro, u"O registro para semestre selecionado não está ativo!", [u"Semestre"]),
        (valida_disciplinas, u"Não é permitido duplicar disciplinas em uma mesma Solicitação", [u"Disciplinas"]),
    ]
    
    _rec_name = "semestre_id"
    
    def create(self, cr, user, vals, context=None):
        if not vals.get("disciplinas_ids", False):
            raise osv.except_osv(u"Disciplinas em falta", u"Não é permitido fazer solicitações sem informar ao menos uma disciplina")
        return super(Solicitacao, self).create(cr, user, vals, context=context)
    
    def write(self, cr, user, ids, vals, context=None):
        if "disciplinas_ids" in vals and not vals.get("disciplinas_ids", False):
            raise osv.except_osv(u"Disciplinas em falta", u"Não é permitido fazer solicitações sem informar ao menos uma disciplina")
        return super(Solicitacao, self).write(cr, user, ids, vals, context=context)
    
    def name_get(self, cr, uid, ids, context=None):
        return [(solic.id, solic.semestre_id.semestre) for solic in self.browse(cr, uid, ids, context=context)]
    
    def ativar(self, cr, uid, ids, context=None):
        disc_ids = []
        for solic in self.read(cr, uid, ids, ["disciplinas_ids"], context=context, load="_classic_write"):
            disc_ids += solic["disciplinas_ids"]
        self.pool.get("ud.monitoria.solicitacao.disciplina").write(cr, uid, disc_ids, {"is_active": True})
        return True
    
    def desativar(self, cr, uid, ids, context=None):
        disc_ids = []
        for solic in self.read(cr, uid, ids, ["disciplinas_ids"], context=context, load="_classic_write"):
            disc_ids += solic["disciplinas_ids"]
        self.pool.get("ud.monitoria.solicitacao.disciplina").write(cr, uid, disc_ids, {"is_active": False})
        return True
