# coding: utf-8
from datetime import datetime
import re

from openerp import SUPERUSER_ID
from openerp.osv import fields, osv, orm
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.translate import _
from openerp.addons.ud.ud import _TIPOS_BOLSA

regex_order = re.compile("^((?:(?:CASE(?: WHEN \w+ *= *'\w+' THEN \d+)+ ELSE \d+ END)|(?:\w+))(?: (?:(?:asc)|(?:desc)))?)(, *(?:(?:CASE(?: WHEN \w+ *= *'\w+' THEN \d+)+ ELSE \d+ END)|(?:\w+))(?: (?:(?:asc)|(?:desc)))?)?$", re.I)
regex_regra = re.compile("CASE .+ ELSE (?P<ord>\d+) END (?P<dir>(?:asc)|(?:desc))?", re.I)
regex_clausula = re.compile("WHEN (?P<campo>\w+) *= *(?P<valor>'\w+') THEN (?P<ord>\d+)", re.I)
regex_espacos = re.compile("\s+")

TIPOS_BOLSA = dict(_TIPOS_BOLSA)


class CriterioAvaliativo(osv.Model):
    _name = "ud.monitoria.criterio.avaliativo"
    _description = u"Critério Avaliativo das inscrições de monitoria (UD)"
    
    def valida_peso(self, cr, uid, ids, context=None):
        for crit in self.browse(cr, uid, ids, context=context):
            if crit.peso <= 0:
                return False
        return True
    
    _columns = {
        "name": fields.char(u"Nome", required=True),
        "peso": fields.float(u"Peso", help=u"Peso usado para calcular a Média Ponderada"),
        "descricao": fields.text(u"Descrição"),
        "processo_seletivo_id": fields.many2one("ud.monitoria.processo.seletivo", u"Processo Seletivo", ondelete="cascade", invisible=True)
    }
    
    _sql_constraints = [
        ("nome_ps_unique", "UNIQUE(name,processo_seletivo_id)", u"Não é permitido registrar critérios avaliativos com nomes iguais em um mesmo Processo Seletivo!"),
    ]
    
    _constraints = [
        (valida_peso, u"O peso do Critério Avaliativo deve ser maior que 0.", [u"Peso"])
    ]
    
    _defaults = {
        "peso": 1,
    }
    
    def create(self, cr, uid, vals, context=None):
        vals["name"] = vals.get("name", u"CITÉRIO").upper()
        return super(CriterioAvaliativo, self).create(cr, uid, vals, context=context)
    
    def write(self, cr, uid, ids, vals, context=None):
        if "name" in vals:
            vals["name"] = vals.get("name", u"CITÉRIO").upper()
        return super(CriterioAvaliativo, self).write(cr, uid, ids, vals, context=context)


class Pontuacao(osv.Model):
    _name = "ud.monitoria.pontuacao"
    _description = u"Pontuação de cada critério (UD)"

    def valida_pontuacao(self, cr, uid, ids, context=None):
        for pontuacao in self.browse(cr, uid, ids, context):
            if pontuacao.pontuacao < 0 and pontuacao.pontuacao > 10:
                return False
        return True

    _columns = {
        "criterio_avaliativo_id": fields.many2one("ud.monitoria.criterio.avaliativo", u"Critério Avaliativo", readonly=True, ondelete="restrict"),
        "pontuacao": fields.float(u"Pontuação", required=True),
        "info": fields.text(u"Informações adicionais"),
        "pontuacoes_disc_id": fields.many2one("ud.monitoria.pontuacoes.disciplina", u"Pontuações de disciplinas", invisible=True, ondelete="cascade"),
    }
    
    _defaults = {
        "pontuacao": 0.,
    }

    _constraints = [
        (valida_pontuacao, u"Toda pontuação deve está entre 0 e 10.", [u"Pontuação"])
    ]
    
    _rec_name = "criterio_avaliativo_id"
    
    def name_get(self, cr, uid, ids, context=None):
        return [(pont.id, u"%s (%d)" % pont.criterio_avaliativo_id.name, pont.pontuacao) for pont in self.browse(cr, uid, ids, context=context)]
    
    def name_search(self, cr, uid, name='', args=None, operator='ilike', context=None, limit=100):
        if not isinstance(args, (list, tuple)):
            args = []
        if not (name == '' and operator == 'ilike'):
            criterios_ids = self.pool.get("ud.monitoria.criterio.avaliativo").search(cr, uid, [("name", operator, name)], context=context)
            args += [("criterio_avaliativo_id", "in", criterios_ids)]
        ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)


class PontuacoesDisciplina(osv.Model):
    _name = "ud.monitoria.pontuacoes.disciplina"
    _description = u"Pontuações/disciplina da inscrição (UD)"
    _order = "disciplina_id"

    def calcula_media(self, cr, uid, ids, campos, args, context=None):
        def media_aritmetica(pontuacoes):
            soma = div = 0
            for pont in pontuacoes:
                soma += pont.pontuacao
                div += 1
            return div and round(soma/div, 2) or 0

        def media_ponderada(pontuacoes):
            soma = div = 0
            for pont in pontuacoes:
                soma += pont.pontuacao * pont.criterio_avaliativo_id.peso
                div += pont.criterio_avaliativo_id.peso
            return div and round(soma/div, 2) or 0
        res = {}
        for pont_disc in self.browse(cr, uid, ids, context=context):
            if pont_disc.inscricao_id.processo_seletivo_id.tipo_media == "a":
                res[pont_disc.id] = media_aritmetica(pont_disc.pontuacoes_ids)
            if pont_disc.inscricao_id.processo_seletivo_id.tipo_media == "p":
                res[pont_disc.id] = media_ponderada(pont_disc.pontuacoes_ids)
        return res
    
    def atualiza_media_pont(self, cr, uid, ids, context=None):
        return [pont.pontuacoes_disc_id.id for pont in self.browse(cr, uid, ids, context) if pont.pontuacoes_disc_id]
    
    def atualiza_media_peso(self, cr, uid, ids, context=None):
        pont_model = self.pool.get("ud.monitoria.pontuacao")
        pont_ids = pont_model.search(cr, uid, [("criterio_avaliativo_id", "in", ids)], context=context)
        return [pont["pontuacoes_disc_id"] for pont in pont_model.read(cr, uid, pont_ids, ["pontuacoes_disc_id"], context=context, load="_classic_write")]
    
    _STATES = [("analise", u"Em Análise"), ("reprovado", u"Reprovado(a)"),
               ("aprovado", u"Aprovado(a)"), ("reserva", u"Cadastro de Reserva")]
    
    _columns = {
        "disciplina_id": fields.many2one("ud.monitoria.disciplina", u"Disciplinas", required=True, ondelete="restrict"),
        "pontuacoes_ids": fields.one2many("ud.monitoria.pontuacao", "pontuacoes_disc_id", u"Pontuações"),
        "media": fields.function(calcula_media, type="float", string=u"Média",
                                 store={"ud.monitoria.pontuacao": (atualiza_media_pont, ["pontuacao"], 10),
                                        "ud.monitoria.criterio.avaliativo": (atualiza_media_peso, ["peso"], 10)},
                                 help=u"Cálculo da média de acordo com os critérios avaliativos do processo seletivo"),
        "state": fields.selection(_STATES, u"Status"),
        "inscricao_id": fields.many2one("ud.monitoria.inscricao", u"Inscrição", invisible=True, ondelete="cascade"),
        "bolsista": fields.related("inscricao_id", "bolsista", type="boolean", string=u"Bolsista", readonly=True),
    }
    
    _defaults = {
        "media": 0.,
    }

    _rec_name = "disciplina_id"
    
    def create(self, cr, uid, vals, context=None):
        vals["state"] = "analise"
        return super(PontuacoesDisciplina, self).create(cr, uid, vals, context=context)
    
    def name_get(self, cr, uid, ids, context=None):
        return [(pont.id, pont.disciplina_id.disciplina_id.name) for pont in self.browse(cr, uid, ids, context=context)]
    
    def name_search(self, cr, uid, name='', args=None, operator='ilike', context=None, limit=100):
        if not isinstance(args, (list, tuple)):
            args = []
        if not (name == '' and operator == 'ilike'):
            disciplinas_ids = self.pool.get("ud.disciplina").search(cr, uid, [("name", operator, name)], context=context)
            args += [("disciplina_id", "in", disciplinas_ids)]
        ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        context = context or {}
        res = super(PontuacoesDisciplina, self).search(cr, uid, args, offset, limit, order, context, count)
        if context.get("filtrar_orientador", False):
            employee = self.pool.get("ud.employee").search(cr, SUPERUSER_ID, [("user_id", "=", uid)], limit=1)
            if employee:
                return [
                    p_disc.id for p_disc in self.browse(cr, uid, res, context)
                    if p_disc.disciplina_id.orientador_id.id == employee[0]
                    ]
            return []
        return res

    def onchange_pontuacoes(self, cr, uid, ids, inscricao_id, pontuacoes_ids, context=None):
        if inscricao_id and pontuacoes_ids:
            criterio_model = self.pool.get("ud.monitoria.criterio.avaliativo")
            pontuacao_model = self.pool.get("ud.monitoria.pontuacao")
            modalidade = self.pool.get("ud.monitoria.inscricao").browse(cr, uid, inscricao_id, context)
            soma = div = 0
            if modalidade.processo_seletivo_id.tipo_media == "a":
                for pont in pontuacoes_ids:
                    if pont[0] == 1:
                        soma += pont[2].get("pontuacao", pontuacao_model.browse(cr, uid, pont[1]).pontuacao)
                    elif pont[0] == 4:
                        soma += pontuacao_model.browse(cr, uid, pont[1]).pontuacao
                    elif pont[0] == 0:
                        soma += pont[2].get("pontuacao", 0)
                    div += 1
            else:
                for pont in pontuacoes_ids:
                    if pont[0] == 1:
                        pontuacao = pontuacao_model.browse(cr, uid, pont[1])
                        peso = pontuacao.criterio_avaliativo_id.peso
                        soma += (pont[2].get("pontuacao", pontuacao.pontuacao) * peso)
                        div += peso
                    elif pont[0] == 4:
                        pontuacao = pontuacao_model.browse(cr, uid, pont[1])
                        peso = pontuacao.criterio_avaliativo_id.peso
                        soma += pontuacao.pontuacao * peso
                        div += peso
                    elif pont[0] == 0:
                        criterio = criterio_model.browse(cr, uid, pont[2].get("criterio_avaliativo_id"))
                        soma += (pont[2].get("pontuacao", 0) * criterio.peso)
                        div += criterio.peso
            return {"value": {"media": div and round(soma / div, 2) or 0}}
        return {"value": {"media": 0}}

    def conf_view(self, cr, uid, res_id, context=None):
        obj_model = self.pool.get('ir.model.data')
        form_id = obj_model.get_object_reference(cr, uid, "ud_monitoria", "ud_monitoria_inscricao_form_view")[1]
        return {
            "name": u"Gerenciamento de Inscrições",
            "view_type": "form",
            "view_mode": "form",
            # "view_id": False,
            "res_model": "ud.monitoria.inscricao",
            "view_id": form_id,
            "type": "ir.actions.act_window",
            "nodestroy": False,
            "res_id": res_id or False,
            "target": "inline",
            "context": context or {},
        }
    
    def aprovar(self, cr, uid, ids, context=None):
        context = context or {}
        perfil_model = self.pool.get("ud.perfil")
        dados_bancarios_model = self.pool.get("ud.dados.bancarios")
        hoje = datetime.strptime(fields.date.context_today(self, cr, uid, context), DEFAULT_SERVER_DATE_FORMAT)
        res_id = False
        for pont in self.browse(cr, uid, ids, context=context):
            media_minima = pont.inscricao_id.processo_seletivo_id.media_minima
            if pont.media < media_minima:
                raise osv.except_osv(u"Média Insuficiente",
                                     u"A média não atingiu o valor mínimo especificado de %.2f" % media_minima)
            res_id = res_id or pont.inscricao_id.id
            state = "n_bolsista"
            if pont.inscricao_id.bolsista:
                if context.pop("sem_bolsa", False):
                    info = u"%s - Inscrição para a disciplina \"%s\" do curso de \"%s\" foi aprovada SEM bolsa." % (
                            datetime.strftime(hoje, "%d-%m-%Y"), pont.disciplina_id.disciplina_id.name,
                            pont.disciplina_id.curso_id.name
                    )
                    self._add_info(pont.inscricao_id, info)
                elif pont.inscricao_id.perfil_id.is_bolsista:
                    raise osv.except_osv(
                        u"Discente bolsista", u"O discente atual está vinculado a uma bolsa do tipo: \"{}\"".format(
                            TIPOS_BOLSA[pont.inscricao_id.perfil_id.tipo_bolsa]
                        )
                    )
                else:
                    # FIXME: O campo do valor da bolsa no núcleo é um CHAR, se possível, mudar para um FLOAT
                    perfil_model.write(cr, SUPERUSER_ID, pont.inscricao_id.perfil_id.id, {
                        "is_bolsista": True, "tipo_bolsa": "m",
                        "valor_bolsa": ("%.2f" % pont.inscricao_id.processo_seletivo_id.valor_bolsa).replace(".", ",")
                    })
                    dados_bancarios_model.write(cr, SUPERUSER_ID, pont.inscricao_id.dados_bancarios_id.id, {
                        "ud_conta_id": pont.inscricao_id.discente_id.id
                    }, context=context)
                    state = "bolsista"
            self._create_doc_discente(cr, pont, state, context)
            self.pool.get("ud.monitoria.documentos.orientador").create(
                cr, SUPERUSER_ID, {"disciplina_id": pont.disciplina_id.id}, context
            )
        self.write(cr, uid, ids, {"state": "aprovado"}, context=context)
        return self.conf_view(cr, uid, res_id, context)

    def aprovar_s_bolsa(self, cr, uid, ids, context=None):
        context = context or {}
        context["sem_bolsa"] = True
        return self.aprovar(cr, uid, ids, context)
    
    def reservar(self, cr, uid, ids, context=None):
        res_id = False
        inscricao_model = self.pool.get("ud.monitoria.inscricao")
        hoje = datetime.strptime(fields.date.context_today(self, cr, uid, context), DEFAULT_SERVER_DATE_FORMAT)
        for pont in self.browse(cr, uid, ids, context=context):
            res_id = res_id or pont.inscricao_id.id
            insc = inscricao_model.browse(cr, uid, pont.inscricao_id.id, context=context)
            info = u"%s - A inscrição para a disciplina \"%s\" do curso de \"%s\" foi selecionada para o cadastro de RESERVA." % (
                    datetime.strftime(hoje, "%d-%m-%Y"), pont.disciplina_id.disciplina_id.name, pont.disciplina_id.curso_id.name)
            if insc.info:
                info = u"%s\n%s" % (insc.info, info)
            inscricao_model.write(cr, uid, insc.id, {"info": info})
            self._create_doc_discente(cr, pont, "reserva", context)
        self.write(cr, uid, ids, {"state": "reserva"}, context=context)
        return self.conf_view(cr, uid, res_id, context)
    
    def reprovar(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {"state": "reprovado"}, context=context)
        return self.conf_view(cr, uid, self.browse(cr, uid, ids, context=context)[0].inscricao_id.id, context)
    
    def _add_info(self, inscricao, info):
        if inscricao.info:
            info = "%s\n%s" %(inscricao.info, info)
        inscricao.write({"info": info})

    def _create_doc_discente(self, cr, browse_self, state, context=None, ativo=True):
        dados = {
            "inscricao_id": browse_self.inscricao_id.id, "tutor": browse_self.inscricao_id.modalidade == "tutor",
            "disciplina_id": browse_self.disciplina_id.id, "state": state, "is_active": ativo
        }
        return self.pool.get("ud.monitoria.documentos.discente").create(cr, SUPERUSER_ID, dados, context)


class Anexo(osv.Model):
    _name = "ud.monitoria.anexo"
    _description = u"Anexo de monitoria (UD)"
    _order = "create_date,name asc"

    _columns = {
        "name": fields.char(u"Nome"),
        "arquivo": fields.binary(u"Arquivo", required=True, filters="*.pdf,*.png,*.jpg,*.jpeg"),
        "processo_seletivo_id": fields.many2one("ud.monitoria.processo.seletivo", u"Processo Seletivo",
                                                ondelete="cascade"),
    }


class ProcessoSeletivo(osv.Model):
    _name = "ud.monitoria.processo.seletivo"
    _description = u"Processo Seletivo de Monitoria (UD)"
    # ATENÇÃO: Esse tipo de ordenação só foi possível porque os métodos "_check_qorder" e "_generate_order_by"
    # foram sobrescritos para atender as necessidades específicas desse modelo
    _order = "CASE WHEN state = 'invalido' THEN 1 "\
             "WHEN state = 'demanda' THEN 2 "\
             "WHEN state = 'andamento' THEN 3 "\
             "WHEN state = 'novo' THEN 4 "\
             "WHEN state = 'encerrado' THEN 5 "\
             "ELSE 10 "\
             "END Asc, name asc"
    
    def atualiza_status_cron(self, cr, uid, context=None):
        ps = self.search(cr, uid, [("state", "in", ["demanda", "novo", "andamento"])])
        if ps:
            context = context or {}
            context["tz"] = "America/Maceio"
            dados = self.status(cr, uid, ps, None, None, context)
            sql = "UPDATE %(tabela)s SET state='%(valor)s' WHERE id=%(id)i;"
            for ps_id in dados:
                cr.execute(sql % {"tabela": self._table, "valor": dados[ps_id], "id": ps_id})
        return True
    
    def status(self, cr, uid, ids, campo, args, context=None):
        res = {}.fromkeys(ids, False)
        hoje = datetime.strptime(fields.date.context_today(self, cr, uid, context), DEFAULT_SERVER_DATE_FORMAT).date()
        for ps in self.browse(cr, uid, ids, context):
            if hoje <= datetime.strptime(ps.prazo_demanda, DEFAULT_SERVER_DATE_FORMAT).date():
                res[ps.id] = "demanda"
            elif ps.disciplinas_ids and ps.anexos_ids:
                if ps.semestre_id.is_active:
                    if hoje < datetime.strptime(ps.data_inicio, DEFAULT_SERVER_DATE_FORMAT).date():
                        res[ps.id] = "novo"
                    elif hoje <= datetime.strptime(ps.data_fim, DEFAULT_SERVER_DATE_FORMAT).date():
                        res[ps.id] = "andamento"
                    else:
                        res[ps.id] = "encerrado"
                else:
                    res[ps.id] = "invalido"
            else:
                res[ps.id] = "invalido"
        return res
    
    def atualiza_status(self, cr, uid, ids, context=None):
        proc_sels = []
        if self._name == "ud.monitoria.registro":
            for reg in self.browse(cr, uid, ids, context):
                proc_sels.extend([ps.id for ps in reg.processos_seletivos_ids])
        elif self._name == "ud.monitoria.processo.seletivo":
            proc_sels.extend(ids)
        hoje = datetime.utcnow().strftime(DEFAULT_SERVER_DATE_FORMAT)
        args = [
            '&', ("id", "in", proc_sels), "|", "|", "|", '|', '|', ("state", "=", "invalido"), ("state", "=", None),
            "&", ("state", "=", "demanda"), ("prazo_demanda", "<", hoje),
            "&", ("state", "=", "novo"), '|', ("prazo_demanda", ">=", hoje), ("data_inicio", "<=", hoje),
            "&", ("state", "=", "andamento"), "|", ("data_inicio", ">", hoje), ("data_fim", "<", hoje),
            "&", ("state", "=", "finalizado"), ("data_fim", ">=", hoje)
        ]
        res = self.pool.get("ud.monitoria.processo.seletivo").search(
            cr, uid, args, context=context
        )
        for ps in self.pool.get("ud.monitoria.processo.seletivo").browse(cr, uid, proc_sels, context):
            if not (ps.anexos_ids and ps.disciplinas_ids):
                res.append(ps.id)
        return res

    def valida_registro(self, cr, uid, ids, context=None):
        for ps in self.browse(cr, uid, ids, context=context):
            if not ps.semestre_id.is_active:
                return False
        return True
    
    def valida_datas(self, cr, uid, ids, context=None):
        for ps in self.browse(cr, uid, ids, context=context):
            data_inicial = datetime.strptime(ps.data_inicio, DEFAULT_SERVER_DATE_FORMAT)
            data_final = datetime.strptime(ps.data_fim, DEFAULT_SERVER_DATE_FORMAT)
            prazo_demanda = datetime.strptime(ps.prazo_demanda, DEFAULT_SERVER_DATE_FORMAT)
            if not (prazo_demanda < data_inicial < data_final):
                return False
        return True

    def valida_bolsa(self, cr, uid, ids, context=None):
        for ps in self.browse(cr, uid, ids, context=context):
            if ps.valor_bolsa < 1:
                return False
        return True

    def valida_criterios_avaliativos(self, cr, uid, ids, context=None):
        for ps in self.browse(cr, uid, ids, context):
            if len(ps.criterios_avaliativos_ids) == 0:
                return False
        return True

    def valida_bolsas_disciplinas(self, cr, uid, ids, context=None):
        for ps in self.browse(cr, uid, ids, context):
            bolsas = {}
            for disc in ps.disciplinas_ids:
                bolsas[disc.curso_id.id] = bolsas.get(disc.curso_id.id, 0) + disc.bolsas
            for dist in ps.semestre_id.distribuicao_bolsas_ids:
                if bolsas.get(dist.curso_id.id, 0) > dist.bolsas:
                    return False
        return True

    _STATES = [("invalido", u"Inválido"), ("demanda", u"Demanda disponível"), ("novo", u"Novo"),
               ("andamento", u"Em Andamento"), ("encerrado", u"Encerrado")]
    
    _columns = {
        "id": fields.integer(u"ID", readonly=True, invisible=True),
        "name": fields.char(u"Nome", required=True),
        "prazo_demanda": fields.date(u"Prazo da demanda", required=True, help=u"Prazo final da demanda"),
        "data_inicio": fields.date(u"Data Inicial", required=True, help=u"Início das inscrições"),
        "data_fim": fields.date(u"Data Final", required=True, help=u"Encerramento das inscrições"),
        "valor_bolsa": fields.float(u"Bolsa (R$)", required=True, help=u"Valor da bolsa"),
        "tipo_media": fields.selection([("a", u"Aritmética"), ("p", u"Ponderada")], u"Tipo de Média", required=True,
                                       help=u"Tipo de média a ser utilizada na aprovação."),
        "media_minima": fields.float(u"Nota Minima", required=True, help=u"Média mínima para aprovação de discentes."),
        "semestre_id": fields.many2one("ud.monitoria.registro", u"Semestre", required=True, ondelete="cascade", help=u"Semestres ativos"),
        "disciplinas_ids": fields.one2many("ud.monitoria.disciplina", "processo_seletivo_id", u"Disciplinas"),
        "anexos_ids": fields.one2many("ud.monitoria.anexo", "processo_seletivo_id", u"Anexos"),
        "inscricoes_ids": fields.one2many("ud.monitoria.inscricao", "processo_seletivo_id", u"Inscrições"),
        "state": fields.function(status, type="selection", selection=_STATES, string=u"Status",
                                 store={
                                     "ud.monitoria.processo.seletivo": (
                                         atualiza_status,
                                         ["prazo_demanda", "data_inicio", "data_fim", "disciplinas_ids", "anexos_ids"],
                                         10
                                     ),
                                     "ud.monitoria.registro": (atualiza_status, ["is_active"], 10)
                                 }),
        "criterios_avaliativos_ids": fields.one2many("ud.monitoria.criterio.avaliativo", "processo_seletivo_id",
                                                     u"Critérios Avaliativos"),
    }
    
    _sql_constraints = [
        ("nome_ps_semestre_unique", "unique(name,semestre_id)",
         u"Não é permitido criar processos seletivos com mesmo nome para o mesmo semestre")
    ]
    
    _constraints = [
        (valida_registro, u"O registro para semestre selecionado não está ativo!", [u"Semestre"]),
        (
            valida_datas,
            u"O prazo da demanda deve ocorrer antes da data inicial e, por sua vez, deve ocorrer antes da data final.",
            [u"Prazo de Demanda, Data Inicial e/ou Data Final"]
         ),
        (valida_bolsa, u"O valor da bolsa não pode ser menor que 1.", [u"Bolsa"]),
        (valida_criterios_avaliativos, u"Deve ser definido ao menos 1 critério avaliativo", [u"Critérios Avaliativos"]),
        (
            valida_bolsas_disciplinas,
            u"A soma total da bolsas das disciplinas não pode ultrapassar o número total de bolsas de seu curso",
            ["Disciplinas"]
        )
    ]
    
    _defaults = {
        "valor_bolsa": 400.,
        "media_minima": 7.0,
        "tipo_media": "p",
        "criterios_avaliativos_ids": [
            (0, 0, {"name": u"PROVA ESCRITA", "peso": 3}),
            (0, 0, {"name": u"MÉDIA FINAL NAS DISCIPLINAS", "peso": 3}),
            (0, 0, {"name": u"COEFICIENTE DE RENDIMENTO", "peso": 2}),
            (0, 0, {"name": u"ENTREVISTA", "peso": 2}),
        ]
    }
    
    def create(self, cr, uid, vals, context=None):
        if "name" in vals:
            vals["name"] = vals.get("name").upper()
        return super(ProcessoSeletivo, self).create(cr, uid, vals, context=context)
    
    def write(self, cr, uid, ids, vals, context=None):
        if "name" in vals:
            vals["name"] = vals.get("name").upper()
        if "data_fim" in vals:
            data_fim = vals["data_fim"]
            for ps in self.browse(cr, uid, ids, context):
                if ps.state in ["andamento", "encerrado"] and data_fim < ps.data_fim:
                    raise osv.except_osv(u"Data Final", u"Nâo é permitido antecipar a data de finalização quando o "
                                                        u"processo seletivo já está em andamento ou encerrado.")
        return super(ProcessoSeletivo, self).write(cr, uid, ids, vals, context=context)

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if (context or {}).get("filtro_coordenador", False):
            grupos = "ud_monitoria.group_ud_monitoria_coordenador,ud_monitoria.group_ud_monitoria_administrador"
            states = []
            if not self.user_has_groups(cr, uid, grupos):
                states.append("invalido")
            grupos += ",ud_monitoria.group_ud_monitoria_coord_disciplina"
            if not self.user_has_groups(cr, uid, grupos):
                states.append("demanda")
            if states:
                args = (args or []) + [("state", "not in", states)]
        return super(ProcessoSeletivo, self).search(cr, uid, args, offset, limit, order, context, count)

    def default_get(self, cr, uid, fields_list, context=None):
        res = super(ProcessoSeletivo, self).default_get(cr, uid, fields_list, context)
        res["semestre_id"] = (context or {}).get("registro_id", False)
        return res

    def _check_qorder(self, word):
        if not regex_order.match(word):
            raise orm.except_orm(_('AccessError'), u"A ordenação do Processo Seletivo não está de acordo com o padrão. Use apenas o nome do campo ou um conjunto de casos seguidos, ou não, de ASC/DESC!")
        return True
    
    def _generate_order_by(self, order_spec, query):
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
            res = super(ProcessoSeletivo, self)._generate_order_by(",".join(outros), query)
            if ord_elementos:
                clausulas = ",".join(ord_elementos)
            if clausulas or res:
                clausulas =  " ORDER BY " + ",".join([(clausulas or ""), (res and res[10:] or "")]).strip(",")
        return clausulas or ''


class Inscricao(osv.Model):
    _name = "ud.monitoria.inscricao"
    _description = u"Inscrição de Monitoria (UD)"
    _order = "state asc, processo_seletivo_id asc, perfil_id asc"
    
    def get_state(self, cr, uid, ids, campo, arg, context=None):
        state = True
        res = {}
        for insc in self.browse(cr, uid, ids, context=context):
            for pont in insc.pontuacoes_ids:
                state = state and pont.state != "analise"
                if not state:
                    break
            res[insc.id] = "concluido" if state else "analise"
        return res
    
    def atualiza_state(self, cr, uid, ids, context=None):
        return map(lambda pont: pont["inscricao_id"], self.read(cr, uid, ids, ["inscricao_id"], context=context, load="_classic_write"))
    
    def valida_registro(self, cr, uid, ids, context=None):
        for insc in self.browse(cr, uid, ids, context=context):
            if not insc.processo_seletivo_id.semestre_id.is_active:
                return False
        return True
    
    _TURNO = [("m", u"Matutino"), ("v", u"Vespertino"), ("n", u"Noturno")]
    
    _MODALIDADE = [("monitor", u"Monitoria"), ("tutor", u"Tutoria")]
    
    _STATES = [("analise", u"Em Análise"), ("concluido", u"Concluída")]
    
    _columns = {
        "id": fields.integer("ID", invisible=True, readonly=True),
        "perfil_id": fields.many2one("ud.perfil", u"Matrícula", required=True, ondelete="restrict"),
        "curso_id": fields.related("perfil_id", "ud_cursos", type="many2one", relation="ud.curso", string=u"Curso",
                                   readonly=True, help="Curso que o discente possui vínculo"),
        "discente_id": fields.related("perfil_id", "ud_papel_id", type="many2one", relation="ud.employee",
                                      string=u"Discente", readonly=True),
        "telefone_fixo": fields.related("perfil_id", "ud_papel_id", "work_phone", type="char"),
        "celular": fields.related("perfil_id", "ud_papel_id", "mobile_phone", type="char"),
        "email": fields.related("perfil_id", "ud_papel_id", "work_email", type="char"),

        "cpf": fields.binary(u"CPF", required=True),
        "cpf_nome": fields.char(u"Arquivo CPF"),
        "identidade": fields.binary(u"RG", required=True),
        "identidade_nome": fields.char(u"Arquivo RG", required=True),
        "hist_analitico": fields.binary(u"Hist. Analítico", required=True),
        "hist_analitico_nome": fields.char(u"Arquivo Hist. Analítico", required=True),
        "processo_seletivo_id": fields.many2one("ud.monitoria.processo.seletivo", u"Processo Seletivo", required=True, ondelete="restrict"),
        "modalidade": fields.selection(_MODALIDADE, u"Modalidade", required=True),
        "turno": fields.selection(_TURNO, u"Turno", required=True),
        "bolsista": fields.boolean(u"Bolsista"),
        "pontuacoes_ids": fields.one2many("ud.monitoria.pontuacoes.disciplina", "inscricao_id", u"Pontuações"),
        "dados_bancarios_id": fields.many2one("ud.dados.bancarios", u"Dados Bancários", ondelete="restrict",
                                              domain="[('ud_conta_id', '=', discente_id)]"),
        "info": fields.text(u"Informações Adicionais", readonly=True),

        "state": fields.function(get_state, type="selection", selection=_STATES, method=True, string=u"Status",
                                 store={"ud.monitoria.pontuacoes.disciplina": (atualiza_state, ["state"], 10)}),
    }
    
    _sql_constraints = [
        ("discente_ps_unique", "unique(perfil_id,processo_seletivo_id)", u"Não é permitido inscrever o mesmo discente multiplas vezes em um mesmo Processo Seletivo!"),
    ]
    
    _constraints = [
        (valida_registro, u"Não é possível realizar as ações desejadas enquanto o processo seletivo estiver vinculado a um registro inativo", [u"Processo Seletivo"]),
    ]

    def name_get(self, cr, uid, ids, context=None):
        return [(insc.id, u"%s (Matrícula: %s)" % (insc.discente_id.name, insc.perfil_id.matricula))
                for insc in self.browse(cr, uid, ids, context=context)]

    def name_search(self, cr, uid, name='', args=None, operator='ilike', context=None, limit=100):
        discentes_ids = self.pool.get("ud.employee").search(cr, uid, [("name", operator, name)], context=context)
        args += [("discente_id", "in", discentes_ids)]
        perfil_model = self.pool.get("ud.perfil")
        for perfil in perfil_model.search(cr, uid, [("matricula", "=", name)]):
            discentes_ids.append(perfil_model.browse(cr, uid, perfil, context).ud_papel_id.id)
        ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        context = context or {}
        pessoa = None
        if context.pop("filtrar_discente", False):
            pessoa= self.pool.get("ud.employee").search(cr, SUPERUSER_ID, [("user_id", "=", uid)], limit=1)
            if pessoa:
                args += [("perfil_id", "in",
                          self.pool.get("ud.perfil").search(cr, SUPERUSER_ID, [("ud_papel_id", "=", pessoa[0])]))]
            else:
                return []
        res = super(Inscricao, self).search(cr, uid, args, offset, limit, order, context, count)
        if context.get("filtrar_orientador", False):
            if not pessoa:
                pessoa = self.pool.get("ud.employee").search(cr, SUPERUSER_ID, [("user_id", "=", uid)], limit=1)
                if not pessoa:
                    return []
            perfis = self.pool.get("ud.perfil").search(cr, SUPERUSER_ID, [("ud_papel_id", "=", pessoa[0])], context=context)
            pontuacoes_model = self.pool.get("ud.monitoria.pontuacoes.disciplina")
            pontuacoes = pontuacoes_model.search(cr, uid, [("inscricao_id", "in", res)], context=context)
            return list(
                set([pont.inscricao_id.id
                     for pont in pontuacoes_model.browse(cr, uid, pontuacoes, context)
                     if pont.disciplina_id.perfil_id.id in perfis]
                    )
            )
        return res

    def onchange_perfil(self, cr, uid, ids, perfil_id, bolsista, context=None):
        value = {"curso_id": False, "discente_id": False, "telefone_fixo": False, "celular": False, "email": False}
        res = {"value": value}
        if perfil_id:
            perfil = self.pool.get("ud.perfil").browse(cr, uid, perfil_id, context=context)
            value["curso_id"] = perfil.ud_cursos.id
            value["discente_id"] = perfil.ud_papel_id.id
            value["telefone_fixo"] = perfil.ud_papel_id.work_phone
            value["celular"] = perfil.ud_papel_id.mobile_phone
            value["email"] = perfil.ud_papel_id.work_email
            if bolsista:
                if perfil.is_bolsista:
                    value["bolsista"] =  False
                    res["warning"] = {"title": u"Discente bolsista",
                                      "message": u"Não é permitido fazer inscrição de discentes registrados como bolsista."}
        return res
