# coding: utf-8

from openerp import SUPERUSER_ID
from openerp.osv import fields, osv, orm
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.translate import _
from datetime import datetime
import re

regex_order = re.compile("^((?:(?:CASE(?: WHEN \w+ *= *'\w+' THEN \d+)+ ELSE \d+ END)|(?:\w+))(?: (?:(?:asc)|(?:desc)))?)(, *(?:(?:CASE(?: WHEN \w+ *= *'\w+' THEN \d+)+ ELSE \d+ END)|(?:\w+))(?: (?:(?:asc)|(?:desc)))?)?$", re.I)
regex_regra = re.compile("CASE .+ ELSE (?P<ord>\d+) END (?P<dir>(?:asc)|(?:desc))?", re.I)
regex_clausula = re.compile("WHEN (?P<campo>\w+) *= *(?P<valor>'\w+') THEN (?P<ord>\d+)", re.I)
regex_espacos = re.compile("\s+")

_BANCOS = [('218',  u'218 - Banco Bonsucesso S.A.'),                       ('036', u'036 - Banco Bradesco BBI S.A'),
           ('204',  u'204 - Banco Bradesco Cartões S.A.'),                 ('237', u'237 - Banco Bradesco S.A.'),
           ('263',  u'263 - Banco Cacique S.A.'),                          ('745', u'745 - Banco Citibank S.A.'),
           ('229',  u'229 - Banco Cruzeiro do Sul S.A.'),                  ('001', u'001 - Banco do Brasil S.A.'),
           ('047',  u'047 - Banco do Estado de Sergipe S.A.'),             ('037', u'037 - Banco do Estado do Pará S.A.'),
           ('041',  u'041 - Banco do Estado do Rio Grande do Sul S.A.'),   ('004', u'004 - Banco do Nordeste do Brasil S.A.'),
           ('184',  u'184 - Banco Itaú BBA S.A.'),                         ('479', u'479 - Banco ItaúBank S.A'),
           ('479A', u'479A - Banco Itaucard S.A.'),                        ('M09', u'M09 - Banco Itaucred Financiamentos S.A.'),
           ('389',  u'389 - Banco Mercantil do Brasil S.A.'),              ('623', u'623 - Banco Panamericano S.A.'),
           ('633',  u'633 - Banco Rendimento S.A.'),                       ('453', u'453 - Banco Rural S.A.'),
           ('422',  u'422 - Banco Safra S.A.'),                            ('033', u'033 - Banco Santander (Brasil) S.A.'),
           ('073',  u'073 - BB Banco Popular do Brasil S.A.'),             ('104', u'104 - Caixa Econômica Federal'),
           ('477',  u'477 - Citibank N.A.'),                               ('399', u'399 - HSBC Bank Brasil S.A. – Banco Múltiplo'),
           ('652',  u'652 - Itaú Unibanco Holding S.A.'),                  ('341', u'341 - Itaú Unibanco S.A.'),
           ('409',  u'409 - UNIBANCO – União de Bancos Brasileiros S.A.'),
        ]


class ProcessoSeletivoDisciplina(osv.Model):
    _name = "ud.monitoria.ps.disciplina"
    _description = u"Disciplina do Processo Seletivo (UD)"
    _inherit = "ud.monitoria.info.disciplina"

    def valida_disciplina_ps(self, cr, uid, ids, context=None):
        for disc in self.browse(cr, uid, ids, context=context):
            if self.search(cr, uid, [("curso_id", "=", disc.curso_id.id), ("disciplina_id", "=", disc.disciplina_id.id),
                                     ("id", "!=", disc.id), ("processo_seletivo_id", "=", disc.processo_seletivo_id.id)], context=context, count=2) > 0:
                return False
        return True
    
    _columns = {
        "monitor_s_bolsa": fields.integer(u"Vagas sem bolsa (Monitor)", required=True),
        "tutor_s_bolsa": fields.integer(u"Vagas sem bolsa (Tutor)", required=True),
        "processo_seletivo_id": fields.many2one("ud.monitoria.processo.seletivo", u"Processo Seletivo", ondelete="cascade"),
    }
    
    _constraints = [
        (valida_disciplina_ps, u"Não é permitido duplicar disciplinas em um mesmo processo seletivo", [u"Disciplinas"]),
    ]
    
    def name_get(self, cr, uid, ids, context=None):
        return [(disc.id, "%s: %s" % (disc.curso_id.name, disc.disciplina_id.name)) for disc in self.browse(cr, uid, ids, context=context)]
     
    def name_search(self, cr, uid, name='', args=None, operator='ilike', context=None, limit=100):
        if not isinstance(args, (list, tuple)):
            args = []
        if not (name == '' and operator == 'ilike'):
            disciplinas_ids = self.pool.get("ud.disciplina").search(cr, uid, [("name", operator, name)], context=context)
            args += [("disciplina_id", "in", disciplinas_ids)]
        ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)
    
    def onchange_siape(self, cr, uid, ids, siape, context=None):
        if siape:
            perfil_model = self.pool.get("ud.perfil")
            papel_id = perfil_model.search(cr, SUPERUSER_ID, [("matricula", "=", siape),
                                                              ("tipo", "=", "p")], context=context)
            if papel_id:
                return {"value": {"orientador_id": perfil_model.read(cr, SUPERUSER_ID, papel_id[0], ["ud_papel_id"], context=context).get("ud_papel_id")}}
        return {"value": {"orientador_id": False, "siape": False},
                "warning": {"title": u"Alerta",
                            "message": u"SIAPE inexistente."}}
    
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
    
    def calcula_media(self, cr, uid, ids, campo, arg, context=None):
        res = {}
        for pont_disc in self.browse(cr, uid, ids, context=context):
            soma, div = 0., 0.
            for pont in pont_disc.pontuacoes_ids:
                if campo == "media_aritmetica":
                    soma += pont.pontuacao
                    div += 1
                elif campo == "media_ponderada":
                    soma += pont.pontuacao * pont.criterio_avaliativo_id.peso
                    div += pont.criterio_avaliativo_id.peso
            res[pont_disc.id] = round(soma/(div or 1), 2)
        return res
    
    def atualiza_media_pont(self, cr, uid, ids, context=None):
        pont_ids = []
        for pont in self.browse(cr, uid, ids, context=context):
            if pont.pontuacoes_disc_id:
                pont_ids.append(pont.pontuacoes_disc_id.id)
        return pont_ids
    
    def atualiza_media_peso(self, cr, uid, ids, context=None):
        pont_model = self.pool.get("ud.monitoria.pontuacao")
        pont_ids = pont_model.search(cr, uid, [("criterio_avaliativo_id", "in", ids)], context=context)
        return [pont["pontuacoes_disc_id"] for pont in pont_model.read(cr, uid, pont_ids, ["pontuacoes_disc_id"], context=context, load="_classic_write")]
    
    _STATES = [("analise", u"Em Análise"), ("reprovado", u"Reprovado(a)"),
               ("aprovado", u"Aprovado(a)"), ("reserva", u"Cadastro de Reserva")]
    
    _columns = {
        "disciplina_id": fields.many2one("ud.monitoria.ps.disciplina", u"Disciplina", required=True, ondelete="restrict"),
        "pontuacoes_ids": fields.one2many("ud.monitoria.pontuacao", "pontuacoes_disc_id", u"Pontuações"),
        "media_aritmetica": fields.function(calcula_media, type="float", string=u"Média Aritmética", method=True,
                                            help=u"∑(pontuaçao)/nº pontuaçoes",
                                            store={"ud.monitoria.pontuacao": (atualiza_media_pont, ["pontuacao"], 10)}),
        "media_ponderada": fields.function(calcula_media, type="float", string=u"Média Ponderada", method=True,
                                           help=u"∑(pontuaçao*peso)/∑(peso)",
                                           store={"ud.monitoria.pontuacao": (atualiza_media_pont, ["pontuacao"], 10),
                                                  "ud.monitoria.criterio.avaliativo": (atualiza_media_peso, ["peso"], 10)}),
        "state": fields.selection(_STATES, u"Status"),
        "inscricao_id": fields.many2one("ud.monitoria.inscricao", u"Inscrição", invisible=True, ondelete="cascade"),
        "bolsista": fields.related("inscricao_id", "bolsista", type="boolean", string=u"Bolsista", readonly=True),
    }
    
    _defaults = {
        "media_aritmetica": 0.,
        "media_ponderada": 0.,
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
    
    def conf_view(self, cr, uid, res_id):
        obj_model = self.pool.get('ir.model.data')
        form_id = obj_model.get_object_reference(cr, uid, "ud_monitoria", "ud_monitoria_inscricao_form_view")[1]
        return {
            "name": u"Gerenciamento de Inscrições",
            "view_type": "form",
            "view_mode": "form",
            "view_id": False,
            "res_model": "ud.monitoria.inscricao",
            "view_id": form_id,
            "type": "ir.actions.act_window",
            "nodestroy": False,
            "res_id": res_id or False,
            "target": "inline",
        }
    
    def aprovar(self, cr, uid, ids, context=None):
        tipos_bolsas = {
            "per": u"Permanência", "pai": u"Painter", "pibic": u"PIBIC-CNPq",
            "pibip": u"PIBIB-Ação", "pibit": u"PIBIT-CNPq", "aux": u"Auxílio Alimentação",
            "aux_t": u"Auxílio Transporte", "bdi": u"BDI",
            "bdai": u"BDAI", "pibid": u"PIBID", "m": u"Monitoria"}
        context = context or {}
        perfil_model = self.pool.get("ud.perfil")
        dados_bancarios_model = self.pool.get("ud.dados.bancarios")
        hoje = datetime.strptime(fields.date.context_today(self, cr, uid, context), DEFAULT_SERVER_DATE_FORMAT)
        res_id = False
        for pont in self.browse(cr, uid, ids, context=context):
            tipo_media = pont.inscricao_id.processo_seletivo_id.semestre_id.tipo_media
            media_minima = pont.inscricao_id.processo_seletivo_id.semestre_id.media_minima
            if tipo_media == "a" and pont.media_aritmetica < media_minima:
                raise osv.except_osv(u"Média Baixa",
                                     u"O valor da média aritmética é abaixo de %.2f" % media_minima)
            elif tipo_media == "p" and pont.media_ponderada < media_minima:
                raise osv.except_osv(u"Média Baixa",
                                     u"O valor da média ponderada é abaixo de %.2f" % media_minima)

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
                        u"Discente bolsista", u"O discente atual possui bolsa do tipo: \"{}\"".format(
                            tipos_bolsas[pont.inscricao_id.perfil_id.tipo_bolsa]
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
            self._get_create_doc_discente(cr, uid, pont, state, context)
        self.write(cr, uid, ids, {"state": "aprovado"}, context=context)
        return self.conf_view(cr, uid, res_id)
    
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
            self._get_create_doc_discente(cr, uid, pont, "reserva", context)
        self.write(cr, uid, ids, {"state": "reserva"}, context=context)
        return self.conf_view(cr, uid, res_id)
    
    def reprovar(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {"state": "reprovado"}, context=context)
        return self.conf_view(cr, uid, self.browse(cr, uid, ids, context=context)[0].inscricao_id.id)
    
    def onchange_pontuacoes(self, cr, uid, ids, pontuacoes_ids, context=None):
        if pontuacoes_ids:
            criterio_model = self.pool.get("ud.monitoria.criterio.avaliativo")
            pontuacao_model = self.pool.get("ud.monitoria.pontuacao")
            soma_a, soma_p, div_a, div_p = 0., 0., 0., 0.
            for pont in pontuacoes_ids:
                if pont[0] == 1:
                    pontuacao = pontuacao_model.browse(cr, uid, pont[1])
                    soma_a += pont[2].get("pontuacao", pontuacao.pontuacao)
                    peso = pontuacao.criterio_avaliativo_id.peso
                    soma_p += (pont[2].get("pontuacao", pontuacao.pontuacao) * peso)
                    div_p += peso
                elif pont[0] == 4:
                    pontuacao = pontuacao_model.browse(cr, uid, pont[1])
                    soma_a += pontuacao.pontuacao
                    peso = pontuacao.criterio_avaliativo_id.peso
                    soma_p += pontuacao.pontuacao * peso
                    div_p += peso
                elif pont[0] == 0:
                    soma_a += pont[2].get("pontuacao", 0)
                    criterio = criterio_model.browse(cr, uid, pont[2].get("criterio_avaliativo_id"))
                    soma_p += (pont[2].get("pontuacao", 0) * criterio.peso)
                    div_p += criterio.peso

                div_a += 1
            return {"value": {"media_aritmetica": round(soma_a/(div_a or 1), 2),
                              "media_ponderada": round(soma_p/(div_p or 1), 2)}}
        return {"value": {"media_aritmetica": 0, "media_ponderada": 0}}

    def _add_info(self, inscricao, info):
        if inscricao.info:
            info = "%s\n%s" %(inscricao.info, info)
        inscricao.write({"info": info})

    def _get_create_discente(self, cr, uid, browse_self, context=None):
        discente_model = self.pool.get("ud.monitoria.discente")
        discente = discente_model.search(cr, uid, [
            ("matricula", "=", browse_self.inscricao_id.perfil_id.matricula),
            ("tipo", "=", browse_self.inscricao_id.perfil_id.tipo)
        ])
        if discente:
            return discente[0]
        dados = {
            "matricula": browse_self.inscricao_id.perfil_id.matricula,
            "tipo": browse_self.inscricao_id.perfil_id.tipo,
        }
        return discente_model.create(cr, uid, dados, context)

    def _get_create_disciplina_monitoria(self, cr, uid, browse_self, context=None):
        """
        Método que busca ou cria um registro de "ud.monitoria.disciplina" a partir dos dados de
        "ud.monitoria.ps.disciplina".

        :param browse_self: Objeto de browse_record de PontuacoesDisciplina.
        :return: id da disciplina.
        """
        disc_model = self.pool.get("ud.monitoria.disciplina")
        disc = disc_model.search(cr, uid, [
            ("disciplina_id", "=", browse_self.disciplina_id.disciplina_id.id),
            ("orientador_id", "=", browse_self.disciplina_id.orientador_id.id),
            ("semestre_id", "=", browse_self.inscricao_id.processo_seletivo_id.semestre_id.id)
        ])
        if disc:
            disc_model.atualiza_orientador(cr, uid, disc, context)
            return disc[0]
        dados = {
            "curso_id": browse_self.disciplina_id.curso_id.id,
            "disciplina_id": browse_self.disciplina_id.disciplina_id.id,
            "siape": browse_self.disciplina_id.siape,
            "orientador_id": browse_self.disciplina_id.orientador_id.id,
            "data_inicial": browse_self.disciplina_id.data_inicial,
            "data_final": browse_self.disciplina_id.data_final,
            "semestre_id": browse_self.inscricao_id.processo_seletivo_id.semestre_id.id,
        }
        return disc_model.create(cr, uid, dados, context)

    def _get_create_doc_discente(self, cr, uid, browse_self, state, context=None):
        doc_discente_model = self.pool.get("ud.monitoria.documentos.discente")
        dados = {
            "inscricao_id": browse_self.inscricao_id.id, "tutor": browse_self.inscricao_id.modalidade == "tutor",
            "disciplina_id": self._get_create_disciplina_monitoria(cr, uid, browse_self, context), "state": state,
            "discente_id": self._get_create_discente(cr, uid, browse_self, context), "bolsista": browse_self.bolsista,
        }
        return doc_discente_model.create(cr, uid, dados, context)


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
    _order = "CASE WHEN state = 'andamento' THEN 1 "\
             "WHEN state = 'invalido' THEN 2 "\
             "WHEN state = 'novo' THEN 3 "\
             "WHEN state = 'encerrado' THEN 4 "\
             "ELSE 10 "\
             "END Asc, name asc"
    
    def atualiza_status_cron(self, cr, uid, context=None):
        ps = self.search(cr, uid, [("state", "in", ["novo", "andamento"])])
        if ps:
            context = context or {}
            context["tz"] = "America/Maceio"
            dados = self.status(cr, uid, ps, None, None, context)
            sql = "UPDATE ud_monitoria_processo_seletivo SET state='%s' WHERE id = %d;"
            for ps_id in dados:
                cr.execute(sql % (dados[ps_id], ps_id))
        return True
    
    def status(self, cr, uid, ids, campo, args, context=None):
        def status(reg_id, opt):
            if registro_model.read(cr, uid, reg_id, ["is_active"], context=context, load="_classic_write")["is_active"]:
                return opt
            return "invalido"
        res = {}.fromkeys(ids, False)
        hoje = datetime.strptime(fields.date.context_today(self, cr, uid, context), DEFAULT_SERVER_DATE_FORMAT).date()
        registro_model = self.pool.get("ud.monitoria.registro")
        for ps in self.read(cr, uid, ids, ["data_inicio", "data_fim", "disciplinas_ids", "anexos_ids", "semestre_id"], context=context, load="_classic_write"):
            if ps["disciplinas_ids"] and ps["anexos_ids"]:
                data_inicio = datetime.strptime(ps["data_inicio"], DEFAULT_SERVER_DATE_FORMAT).date()
                data_fim = datetime.strptime(ps["data_fim"], DEFAULT_SERVER_DATE_FORMAT).date()
                if hoje < data_inicio:
                    res[ps["id"]] = status(ps["semestre_id"], "novo")
                elif hoje <= data_fim:
                    res[ps["id"]] = status(ps["semestre_id"], "andamento")
                else:
                    res[ps["id"]] = "encerrado"
            else:
                res[ps["id"]] = "invalido"
        return res
    
    def atualiza_status(self, cr, uid, ids, context=None):
        cond_add = ""
        if ids:
            if self._name == "ud.monitoria.registro":
                cond_add = "reg.id in (%s) AND " % str(ids)[1:-1].rstrip(",").replace("L", "")
            elif self._name == "ud.monitoria.processo.seletivo":
                cond_add = "ps.id in (%s) AND " % str(ids)[1:-1].rstrip(",").replace("L", "")
        context = context or {}
        context["tz"] = "America/Maceio"
        hoje = fields.date.context_today(self, cr, uid, context)
        sql = """SELECT ps.id FROM ud_monitoria_processo_seletivo ps, ud_monitoria_registro reg
                 WHERE
                    {condicao}ps.semestre_id = reg.id
                    AND (
                        ps.state is null
                        OR ps.state != 'invalido'
                        AND (
                            (SELECT count(*) FROM ud_monitoria_ps_disciplina disc WHERE disc.processo_seletivo_id = ps.id) = 0
                            OR (SELECT count(*) FROM ud_monitoria_anexo anexo WHERE anexo.processo_seletivo_id = ps.id) = 0
                        )
                        OR reg.is_active = False AND ps.data_fim >= '{hoje}'
                        OR (SELECT count(*) FROM ud_monitoria_ps_disciplina disc WHERE disc.processo_seletivo_id = ps.id) > 0
                        AND (SELECT count(*) FROM ud_monitoria_anexo anexo WHERE anexo.processo_seletivo_id = ps.id) > 0
                        AND (
                            ps.state = 'novo' AND NOT ps.data_inicio > '{hoje}'
                            OR ps.state = 'andamento' AND NOT (ps.data_inicio <= '{hoje}' AND ps.data_fim >= '{hoje}')
                            OR ps.state = 'encerrado' AND NOT ps.data_fim < '{hoje}'
                            OR ps.state = 'invalido'
                        )
                    );""".format(hoje=hoje, condicao=cond_add)
        cr.execute(sql)
        return map(lambda l: l[0], cr.fetchall())
    
    def valida_registro(self, cr, uid, ids, context=None):
        for ps in self.browse(cr, uid, ids, context=context):
            if not ps.semestre_id.is_active:
                return False
        return True
    
    def valida_datas(self, cr, uid, ids, context=None):
        for ps in self.browse(cr, uid, ids, context=context):
            if datetime.strptime(ps.data_inicio, DEFAULT_SERVER_DATE_FORMAT) >= datetime.strptime(ps.data_fim, DEFAULT_SERVER_DATE_FORMAT):
                return False
        return True

    def valida_bolsa(self, cr, uid, ids, context=None):
        for ps in self.browse(cr, uid, ids, context=context):
            if ps.valor_bolsa < 1:
                return False
        return True
    
    _STATES = [("invalido", u"Inválido"), ("novo", u"Novo"), ("andamento", u"Em Andamento"), ("encerrado", u"Encerrado")]
    
    _columns = {
        "name": fields.char(u"Nome", required=True),
        "data_inicio": fields.date(u"Data Inicial", required=True, help=u"Início das inscrições"),
        "data_fim": fields.date(u"Data Final", required=True, help=u"Encerramento das inscrições"),
        "valor_bolsa": fields.float(u"Bolsa (R$)", required=True, help=u"Valor da bolsa"),
        "semestre_id": fields.many2one("ud.monitoria.registro", u"Semestre", required=True, ondelete="restrict",
                                       domain=[("is_active", "=", True)], help=u"Semestres ativos"),
        "disciplinas_ids": fields.one2many("ud.monitoria.ps.disciplina", "processo_seletivo_id", u"Disciplinas"),
        "anexos_ids": fields.one2many("ud.monitoria.anexo", "processo_seletivo_id", u"Anexos"),
        "inscricoes_ids": fields.one2many("ud.monitoria.inscricao", "processo_seletivo_id", u"Inscrições", readonly=True),
        "state": fields.function(status, type="selection", selection=_STATES, string=u"Status",
                                 store={"ud.monitoria.processo.seletivo": (atualiza_status, ["data_inicio", "data_fim", "disciplinas_ids", "anexos_ids"], 10),
                                        "ud.monitoria.registro": (atualiza_status, ["is_active"], 10)}),
        "criterios_avaliativos_ids": fields.one2many("ud.monitoria.criterio.avaliativo", "processo_seletivo_id",
                                                     u"Critérios Avaliativos"),
    }
    
    _sql_constraints = [
        ("nome_ps_semestre_unique", "unique(name,semestre_id)", u"Não é permitido criar processos seletivos com mesmo nome para o mesmo semestre")
    ]
    
    _constraints = [
        (valida_registro, u"O registro para semestre selecionado não está ativo!", [u"Semestre"]),
        (valida_datas, u"A data inicial do processo seletivo deve ocorrer antes da final", [u"Data Inicial e Data Final"]),
        (valida_bolsa, u"O valor da bolsa não pode ser menor que 1.", [u"Bolsa"]),
    ]
    
    _defaults = {
        "valor_bolsa": 400.,
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
        return super(ProcessoSeletivo, self).write(cr, uid, ids, vals, context=context)
    
    def unlink(self, cr, uid, ids, context=None):
        anexos_ids = []
        disc_ids = []
        for ps in self.read(cr, uid, ids, ["anexos_ids", "disciplinas_ids"], context=context):
            anexos_ids += ps["anexos_ids"]
            disc_ids += ps["disciplinas_ids"]
        self.pool.get("ud.monitoria.ps.disciplina").unlink(cr, uid, disc_ids, context=context)
        super(ProcessoSeletivo, self).unlink(cr, uid, ids, context=context)
        self.pool.get("ud.monitoria.anexo").unlink(cr, uid, anexos_ids, context=context)
        return True
    
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
    
    def onchange_semestre(self, cr, uid, ids, semestre_id, disciplinas_ids, context=None):
        if semestre_id:
            disc_model = self.pool.get("ud.monitoria.ps.disciplina")
            registro_model = self.pool.get("ud.monitoria.registro")
            discs = []
            for disc in disciplinas_ids:
                if disc[0] == 0:
                    discs.append((disc[-1]["curso_id"], disc[-1]["disciplina_id"]))
                elif disc[0] == 1:
                    d = disc_model.browse(cr, uid, disc[1])
                    discs.append((disc[-1].get("curso_id", d.curso_id.id), disc[-1].get("disciplina_id", d.disciplina_id.id)))
                elif disc[0] == 4:
                    d = disc_model.browse(cr, uid, disc[1])
                    discs.append((d.curso_id.id, d.disciplina_id.id))
            for solicitacao in registro_model.browse(cr, uid, semestre_id, context=context).demanda_ids:
                for disc in solicitacao.disciplinas_ids:
                    if disc.is_active and (disc.curso_id.id, disc.disciplina_id.id) not in discs:
                        disciplinas_ids.append(
                            (0, 0, {"curso_id": disc.curso_id.id, "disciplina_id": disc.disciplina_id.id,
                                    "siape": disc.siape, "orientador_id": disc.orientador_id.id,
                                    "data_inicial": disc.data_inicial, "data_final": disc.data_final, "is_active": True,
                                    "monitor_s_bolsa": disc.monitor_s_bolsa, "tutor_s_bolsa": disc.tutor_s_bolsa,
                                    "num_bolsas": disc.num_bolsas})
                        )
            return {"value": {"disciplinas_ids": disciplinas_ids}}
        return {}


class Inscricao(osv.Model):
    _name = "ud.monitoria.inscricao"
    _description = u"Inscrição de Monitoria (UD)"
    _order = "state asc, processo_seletivo_id asc, matricula asc, perfil_id asc"
    
    def _get_perfil(self, cr, uid, ids, campo, arg, context=None):
        perfil_model = self.pool.get("ud.perfil")
        res = {}
        for inf_disc in self.read(cr, uid, ids, ["matricula"], context=context, load="_classic_write"):
            papel_id = perfil_model.search(cr, SUPERUSER_ID, [("matricula", "=", inf_disc["matricula"]),
                                                                ("tipo", "=", "a")], context=context)
            if papel_id:
                res[inf_disc.get("id")] = papel_id[0]
        return res
    
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
    
    def _valida_matricula(self, cr, uid, ids, context=None):
        perfil_model = self.pool.get("ud.perfil")
        for insc in self.browse(cr, uid, ids, context=context):
            papel_id = perfil_model.search(cr, SUPERUSER_ID, [("matricula", "=", insc.matricula),
                                                                ("tipo", "=", "a")], context=context)
            if not papel_id:
                return False
        return True
    
    def valida_registro(self, cr, uid, ids, context=None):
        for insc in self.browse(cr, uid, ids, context=context):
            if not insc.processo_seletivo_id.semestre_id.is_active:
                return False
        return True
    
    _TURNO = [("m", u"Matutino"), ("v", u"Vespertino"), ("n", u"Noturno")]
    
    _MODALIDADE = [("monitor", u"Monitoria"), ("tutor", u"Tutoria")]
    
    _STATES = [("analise", u"Em Análise"), ("concluido", u"Concluída")]
    
    _columns = {
        "matricula": fields.char(u"Matrícula", size=15, required=True),
        "perfil_id": fields.function(_get_perfil, type="many2one", relation="ud.perfil", string=u"Perfil", method=True, invisible=True,
                                     store={"ud.monitoria.inscricao": (lambda self, cr, uid, ids, context=None: ids, ["matricula"], 10)}),
        "curso_id": fields.related("perfil_id", "ud_cursos", type="many2one", relation="ud.curso", string=u"Curso",
                                   readonly=True, help="Curso que o discente possui vínculo"),
        "discente_id": fields.related("perfil_id", "ud_papel_id", type="many2one", relation="ud.employee",
                                      string=u"Discente", readonly=True),
        
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
        "disciplinas_ids": fields.many2many("ud.monitoria.ps.disciplina", "ud_monitoria_disc_inscricao_rel", "inscricao_id", "disciplina_id",
                                            string=u"Disciplinas", domain="[('processo_seletivo_id', '=', processo_seletivo_id)]", required=True),
        "pontuacoes_ids": fields.one2many("ud.monitoria.pontuacoes.disciplina", "inscricao_id", u"Pontuações"),
        "dados_bancarios_id": fields.many2one("ud.dados.bancarios", u"Dados Bancários", ondelete="restrict"),
        "info": fields.text(u"Informações Adicionais", readonly=True),
        "state": fields.function(get_state, type="selection", selection=_STATES, method=True, string=u"Status",
                                 store={"ud.monitoria.pontuacoes.disciplina": (atualiza_state, ["state"], 10)}),
    }
    
    _sql_constraints = [
        ("discente_ps_unique", "unique(matricula,perfil_id,processo_seletivo_id)", u"Não é permitido inscrever o mesmo discente multiplas vezes em um mesmo Processo Seletivo!"),
    ]
    
    _constraints = [
        (valida_registro, u"Não é possível realizar as ações desejadas enquanto o processo seletivo estiver vinculado a um registro inativo", [u"Processo Seletivo"]),
        (_valida_matricula, u"Matrícula Inexistente", [u"Matrícula"]),
    ]

    def name_get(self, cr, uid, ids, context=None):
        return [(insc.id, insc.discente_id.name) for insc in self.browse(cr, uid, ids, context=context)]
    
    def name_search(self, cr, uid, name='', args=None, operator='ilike', context=None, limit=100):
        if not isinstance(args, (list, tuple)):
            args = []
        if not (name == '' and operator == 'ilike'):
            discentes_ids = self.pool.get("ud.employee").search(cr, uid, [("name", operator, name)], context=context)
            args += [("discente_id", "in", discentes_ids)]
        ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        context = context or {}
        if context.pop("filtrar_discente", False):
            employee= self.pool.get("ud.employee").search(cr, SUPERUSER_ID, [("user_id", "=", uid)], limit=1)
            if employee:
                args += [("perfil_id", "in",
                          self.pool.get("ud.perfil").search(cr, SUPERUSER_ID, [("ud_papel_id", "=", employee)]))]
            else:
                return []
        return super(Inscricao, self).search(cr, uid, args, offset, limit, order, context, count)

    def onchange_matricula(self, cr, uid, ids, matricula, bolsista, context=None):
        res = {}
        if matricula:
            perfil_model = self.pool.get("ud.perfil")
            papel_id = perfil_model.search(cr, SUPERUSER_ID, [("matricula", "=", matricula),
                                                              ("tipo", "=", "a")], context=context)
            if papel_id:
                perfil = perfil_model.browse(cr, uid, papel_id[0], context=context)
                res = {"value": {"perfil_id": papel_id[0], "discente_id": perfil.ud_papel_id.id, "curso_id": perfil.ud_cursos}}
                if bolsista:
                    if perfil.is_bolsista:
                        res["value"]["bolsista"] =  False
                        res["warning"] = {"title": u"Discente bolsista",
                                          "message": u"Não é permitido fazer inscrição de discentes registrados como bolsista."}
            else:
                res = {"value": {"matricula": False, "perfil_id": False, "discente_id": False, "curso_id": False},
                       "warning": {"title": u"Alerta",
                                   "message": u"Matrícula inexistente."}}
        return res

    def onchange_pontuacoes(self, cr, uid, ids, pontuacoes, context=None):
        for pontuacao in [pont[2] for pont in pontuacoes if pont[0] == 1]:
            pontuacao.update(self.pool.get("ud.monitoria.pontuacoes.disciplina").onchange_pontuacoes(
                cr, uid, None, pontuacao["pontuacoes_ids"])["value"]
            )
        return {"value": {"pontuacoes_ids": pontuacoes}}
