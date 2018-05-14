# coding: utf-8
from datetime import datetime
from openerp import SUPERUSER_ID
from openerp.osv import fields, osv
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.addons.ud.ud import _TIPOS_BOLSA
from util import get_ud_pessoa_id, data_hoje


TIPOS_BOLSA = dict(_TIPOS_BOLSA)


class Pontuacao(osv.Model):
    _name = "ud_monitoria.pontuacao"
    _description = u"Pontuação de cada critério (UD)"
    _rec_name = "criterio_avaliativo_id"
    _columns = {
        "criterio_avaliativo_id": fields.many2one("ud_monitoria.criterio_avaliativo", u"Critério Avaliativo",
                                                  readonly=True, ondelete="restrict"),
        "pontuacao": fields.float(u"Pontuação", required=True),
        "info": fields.text(u"Informações adicionais"),
        "pontuacoes_disc_id": fields.many2one("ud_monitoria.pontuacoes_disciplina", u"Pontuações de disciplinas",
                                              invisible=True, ondelete="cascade"),
    }
    _defaults = {
        "pontuacao": 0.,
    }
    _constraints = [
        (lambda cls, *args, **kwargs: cls.valida_pontuacao(*args, **kwargs),
         u"Toda pontuação deve está entre 0 e 10.", [u"Pontuação"])
    ]

    # Métodos sobrescritos
    def name_get(self, cr, uid, ids, context=None):
        """
        === Sobrescrita do método osv.Model.name_get
        Define a forma de visualização desse modelo em campos many2one.
        """
        return [(pont.id, u"%s (%d)" % pont.criterio_avaliativo_id.name, pont.pontuacao) for pont in
                self.browse(cr, uid, ids, context=context)]

    def name_search(self, cr, uid, name='', args=None, operator='ilike', context=None, limit=100):
        """
        === Sobrescrita do método osv.Model.name_search
        Define a forma de pesquisa desse modelo em campos many2one.
        """
        if not isinstance(args, (list, tuple)):
            args = []
        if not (name == '' and operator == 'ilike'):
            criterios_ids = self.pool.get("ud_monitoria.criterio_avaliativo").search(cr, uid,
                                                                                     [("name", operator, name)],
                                                                                     context=context)
            args += [("criterio_avaliativo_id", "in", criterios_ids)]
        ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)

    # Validadores
    def valida_pontuacao(self, cr, uid, ids, context=None):
        """
        Verifica se a pontuação dada está entre 0 e 10.
        """
        for pontuacao in self.browse(cr, uid, ids, context):
            if pontuacao.pontuacao < 0 and pontuacao.pontuacao > 10:
                return False
        return True


class PontuacoesDisciplina(osv.Model):
    _name = "ud_monitoria.pontuacoes_disciplina"
    _description = u"Pontuações/disciplina da inscrição (UD)"
    _order = "disciplina_id"
    _rec_name = "disciplina_id"
    _STATES = [("analise", u"Em Análise"), ("reprovado", u"Reprovado(a)"),
               ("aprovado", u"Aprovado(a)"), ("reserva", u"Cadastro de Reserva")]

    # Metódos para campos calculados
    def calcula_media(self, cr, uid, ids, campos, args, context=None):
        """
        Calcula a média das pontuações dessa disciplina.
        """
        def media_aritmetica(pontuacoes):
            soma = div = 0
            for pont in pontuacoes:
                soma += pont.pontuacao
                div += 1
            return div and round(soma / div, 2) or 0

        def media_ponderada(pontuacoes):
            soma = div = 0
            for pont in pontuacoes:
                soma += pont.pontuacao * pont.criterio_avaliativo_id.peso
                div += pont.criterio_avaliativo_id.peso
            return div and round(soma / div, 2) or 0

        res = {}
        for pont_disc in self.browse(cr, uid, ids, context=context):
            if pont_disc.inscricao_id.processo_seletivo_id.tipo_media == "a":
                res[pont_disc.id] = media_aritmetica(pont_disc.pontuacoes_ids)
            if pont_disc.inscricao_id.processo_seletivo_id.tipo_media == "p":
                res[pont_disc.id] = media_ponderada(pont_disc.pontuacoes_ids)
        return res

    def atualiza_media_pont(self, cr, uid, ids, context=None):
        """
        Gatilho para atualizar a pontuação dada a algum critério avaliativo dessa disciplina.
        """
        return [pont.pontuacoes_disc_id.id for pont in self.browse(cr, uid, ids, context) if pont.pontuacoes_disc_id]

    def atualiza_media_peso(self, cr, uid, ids, context=None):
        """
        Gatilho para atualizar a média o peso de caso algum critério avaliativo do processo seletivo seja alterado.
        """
        pont_model = self.pool.get("ud_monitoria.pontuacao")
        pont_ids = pont_model.search(cr, uid, [("criterio_avaliativo_id", "in", ids)], context=context)
        return [pont["pontuacoes_disc_id"] for pont in
                pont_model.read(cr, uid, pont_ids, ["pontuacoes_disc_id"], context=context, load="_classic_write")]

    _columns = {
        "disciplina_id": fields.many2one('ud_monitoria.disciplina_ps', u"Disciplina", required=True, ondelete="restrict"),
        "pontuacoes_ids": fields.one2many("ud_monitoria.pontuacao", "pontuacoes_disc_id", u"Pontuações"),
        "media": fields.function(
            calcula_media, type="float", string=u"Média",
            store={"ud_monitoria.pontuacao": (atualiza_media_pont, ["pontuacao"], 10),
                   "ud_monitoria.criterio.avaliativo": (atualiza_media_peso, ["peso"], 10)},
            help=u"Cálculo da média de acordo com os critérios avaliativos do processo seletivo"
        ),
        "state": fields.selection(_STATES, u"Status"),
        "inscricao_id": fields.many2one("ud_monitoria.inscricao", u"Inscrição", invisible=True, ondelete="cascade"),
        "bolsista": fields.related("inscricao_id", "bolsista", type="boolean", string=u"Bolsista", readonly=True),
    }
    _defaults = {
        "media": 0.,
    }

    # Métodos sobrescritos
    def create(self, cr, uid, vals, context=None):
        """
        === Extensão do método osv.Model.create
        Valor de "state" padrão passa a ser analise.
        """
        vals["state"] = "analise"
        return super(PontuacoesDisciplina, self).create(cr, uid, vals, context=context)

    def name_get(self, cr, uid, ids, context=None):
        """
        === Sobrescrita do método osv.Model.name_get
        Em campos many2one, o nome da pontuação será o nome de sua disciplina.
        """
        return [(pont.id, pont.disciplina_id.disciplina_id.name) for pont in self.browse(cr, uid, ids, context=context)]

    def name_search(self, cr, uid, name='', args=None, operator='ilike', context=None, limit=100):
        """
        === Sobrescrita do método osv.Model.name_search
        Em campos many2one relacionados ao atual modelo, os valores informados serão pesquisados a partir do nome da
        disciplina desse objeto.
        """
        if not isinstance(args, (list, tuple)):
            args = []
        if not (name == '' and operator == 'ilike'):
            disciplinas_ids = self.pool.get("ud.disciplina").search(cr, uid, [("name", operator, name)],
                                                                    context=context)
            args += [("disciplina_id", "in", disciplinas_ids)]
        ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        """
        === Extensão do método osv.Model.search
        Adicionado a opção de filtrar as pontuações para as disciplinas que o usuário logado estiver sido definido como
        orientador.
        """
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

    # Métodos executados ao modificar valor de campo na view
    def onchange_pontuacoes(self, cr, uid, ids, inscricao_id, pontuacoes_ids, context=None):
        """
        Usado para atualizar a média ao atualizar as pontuações de cada critério avaliativo.

        :param inscricao_id: ID da inscrição
        :param pontuacoes_ids: IDs das pontuações
        :return:
        """
        if inscricao_id and pontuacoes_ids:
            criterio_model = self.pool.get("ud_monitoria.criterio_avaliativo")
            pontuacao_model = self.pool.get("ud_monitoria.pontuacao")
            modalidade = self.pool.get("ud_monitoria.inscricao").browse(cr, uid, inscricao_id, context)
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

    # Métodos para ação de botões
    def aprovar(self, cr, uid, ids, context=None):
        """
        Aplica o status de aprovado ao registro pontuação atual e cria um documento de discente para a disciplina
        correspondente. Se a inscrição tiver sido para bolsista e em context for informado para aprovar sem bolsa,
        essa será aprovada e a informação é adicionada na inscrição.

        :raise osv.except_osv: Caso a média esteja abaixo da definida no processo seletivo ou se o discente se inscreveu
                               como bolsista  e já possua vínculo com outra bolsa.
        """
        context = context or {}
        perfil_model = self.pool.get("ud.perfil")
        dados_bancarios_model = self.pool.get("ud.dados.bancarios")
        hoje = data_hoje(self, cr, uid)
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
                        pont.disciplina_id.bolsas_curso_id.curso_id.name
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
            self.novo_doc_discente(cr, pont, state, context)
            self.doc_orientador(cr, pont, context)
        self.write(cr, uid, ids, {"state": "aprovado"}, context=context)
        return True
        # return self.conf_view(cr, uid, res_id, context)

    def aprovar_s_bolsa(self, cr, uid, ids, context=None):
        """
        Aplica o status de aprovado ao registro de pontuação atual, cria um documento para o discente na disciplina
        correspondente e adiciona a informação de que aprovou um discente que se inscreveu como bolsista mas foi aprovado
        sem bolsa.

        :raise osv.except_osv: Caso a média esteja abaixo da definida no processo seletivo.
        """
        context = context or {}
        context["sem_bolsa"] = True
        return self.aprovar(cr, uid, ids, context)

    def reservar(self, cr, uid, ids, context=None):
        """
        Aplica o status de reserva ao registro de pontuação atual e adiciona a informação na inscrição.
        """
        res_id = False
        hoje = data_hoje(self, cr, uid)
        for pont in self.browse(cr, uid, ids, context=context):
            res_id = res_id or pont.inscricao_id.id
            insc = pont.inscricao_id
            info = u'%s - A inscrição para a disciplina "%s" do curso de "%s" foi selecionada para o cadastro de RESERVA.' % (
                datetime.strftime(hoje, '%d-%m-%Y'), pont.disciplina_id.disciplina_id.name,
                pont.disciplina_id.bolsas_curso_id.curso_id.name)
            if insc.info:
                info = u"%s\n%s" % (insc.info, info)
            insc.write({"info": info})
            self.novo_doc_discente(cr, pont, "reserva", context=context, ativo=False)
        self.write(cr, uid, ids, {"state": "reserva", 'is_active': False}, context=context)
        return True
        # return self.conf_view(cr, uid, res_id, context)

    def reprovar(self, cr, uid, ids, context=None):
        """
        Aplica o status de reprovado ao registro de pontuação atual.
        """
        self.write(cr, uid, ids, {'state': 'reprovado', 'is_active': False}, context=context)
        return True
        # return self.conf_view(cr, uid, self.browse(cr, uid, ids, context=context)[0].inscricao_id.id, context)

    # Outros métodos
    def _add_info(self, inscricao, info):
        """
        Acrescenta informações ao campo "info" de inscrição.

        :param inscricao: Objeto browser de inscrição.
        :param info: String a ser incrementada.
        """
        if inscricao.info:
            info = "%s\n%s" % (inscricao.info, info)
        inscricao.write({"info": info})

    def doc_orientador(self, cr, pontuacao_disc, context=None):
        """
        Verifica se há uma instância de DocumentosOrientador correspondente. Se não, cria uma.
        """
        doc_orientador = self.pool.get('ud_monitoria.documentos_orientador')
        args = [('disciplina_id', '=', pontuacao_disc.disciplina_id.disc_monit_id.id),
                ('perfil_id', '=', pontuacao_disc.disciplina_id.perfil_id.id)]
        if not doc_orientador.search(cr, SUPERUSER_ID, args, context=context, limit=1):
            dados = {
                'disciplina_id':pontuacao_disc.disciplina_id.disc_monit_id.id,
                'perfil_id': pontuacao_disc.disciplina_id.perfil_id.id,
            }
            doc_orientador.create(cr, SUPERUSER_ID, dados, context)

    def novo_doc_discente(self, cr, pontuacao_disc, state, ativo=True, context=None):
        """
        Cria um novo documento de discente ativo ou não, depende dos parâmetros.

        :param browse_self: Objeto browse de Pontuação de Disciplina
        :param state: Status do documento criado
        :param ativo: True ou False para definir se o documento estará ativo
        :return: ID do registro criado.
        """
        dados = {
            'perfil_id': pontuacao_disc.inscricao_id.perfil_id.id,
            'dados_bancarios_id': pontuacao_disc.inscricao_id.dados_bancarios_id.id,
            'disciplina_id':pontuacao_disc.disciplina_id.disc_monit_id.id,
            'tutor': True if pontuacao_disc.inscricao_id.modalidade == 'tutor' else False,
            'state': state,
            "is_active": ativo
        }
        return self.pool.get('ud_monitoria.documentos_discente').create(cr, SUPERUSER_ID, dados, context)

    def conf_view(self, cr, uid, res_id, context=None):
        """
        Configuração de redirecionamento para uma nova tela.
        """
        obj_model = self.pool.get('ir.model.data')
        form_id = obj_model.get_object_reference(cr, uid, "ud_monitoria", "ud_monitoria_inscricao_form")[1]
        return {
            "name": u"Gerenciamento de Inscrições",
            "view_type": "form",
            "view_mode": "form",
            # "view_id": False,
            "res_model": "ud_monitoria.inscricao",
            "view_id": form_id,
            "type": "ir.actions.act_window",
            "nodestroy": False,
            "res_id": res_id or False,
            "target": "inline",
            "context": context or {},
        }


class Inscricao(osv.Model):
    _name = "ud_monitoria.inscricao"
    _description = u"Inscrição de Monitoria (UD)"
    _order = "state asc, processo_seletivo_id asc, perfil_id asc"
    _TURNO = [("m", u"Matutino"), ("v", u"Vespertino"), ("n", u"Noturno")]
    _MODALIDADE = [("monitor", u"Monitoria"), ("tutor", u"Tutoria")]
    _STATES = [("analise", u"Em Análise"), ("concluido", u"Concluída")]

    # Métodos para campos calculados
    def get_state(self, cr, uid, ids, campo, arg, context=None):
        """
        Define o status da inscrição.
        """
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
        """
        Gatilho utilizando para atualizar o status da inscrição quando o status de alguma das pontuações correspondentes
        for modificado.
        """
        return map(lambda pont: pont["inscricao_id"],
                   self.read(cr, uid, ids, ["inscricao_id"], context=context, load="_classic_write"))

    _columns = {
        'id': fields.integer('ID', invisible=True, readonly=True),
        'perfil_id': fields.many2one('ud.perfil', u'Matrícula', required=True, ondelete='restrict'),
        'curso_id': fields.related('perfil_id', 'ud_cursos', type='many2one', relation='ud.curso', string=u'Curso',
                                   readonly=True, help='Curso que o discente possui vínculo'),
        'discente_id': fields.related('perfil_id', 'ud_papel_id', type='many2one', relation='ud.employee',
                                      string=u'Discente', readonly=True),
        'telefone_fixo': fields.related('perfil_id', 'ud_papel_id', 'work_phone', string='Telefone', type='char', readonly=True),
        'celular': fields.related('perfil_id', 'ud_papel_id', 'mobile_phone', string='Celular', type='char', readonly=True),
        'email': fields.related('perfil_id', 'ud_papel_id', 'work_email', string='E-mail', type='char', readonly=True),
        'whatsapp': fields.char(u'WhatsApp', size=15, required=True, readonly=True),

        'cpf_nome': fields.char(u'Arquivo CPF'),
        'identidade_nome': fields.char(u'Arquivo RG'),
        'hist_analitico_nome': fields.char(u'Arquivo Hist. Analítico'),
        'certidao_vinculo_nome': fields.char(u'Arquivo Certidão de Vínculo'),
        'cpf': fields.binary(u'CPF', required=True),
        'identidade': fields.binary(u'RG', required=True),
        'hist_analitico': fields.binary(u'Hist. Analítico', required=True),
        'certidao_vinculo': fields.binary(u'Certidão de Vínculo', required=True),
        'processo_seletivo_id': fields.many2one('ud_monitoria.processo_seletivo', u'Processo Seletivo', required=True,
                                                ondelete='restrict'),
        'modalidade': fields.selection(_MODALIDADE, u'Modalidade', required=True),
        'turno': fields.selection(_TURNO, u'Turno', required=True),
        'bolsista': fields.boolean(u'Bolsista'),
        'pontuacoes_ids': fields.one2many('ud_monitoria.pontuacoes_disciplina', 'inscricao_id', u'Pontuações'),
        'dados_bancarios_id': fields.many2one('ud.dados.bancarios', u'Dados Bancários', ondelete='restrict',
                                              domain='[("ud_conta_id", "=", discente_id)]'),
        'info': fields.text(u'Informações Adicionais', readonly=True),
        'state': fields.function(get_state, type='selection', selection=_STATES, string=u'Status', method=True,
                                 store={'ud_monitoria.pontuacoes_disciplina': (atualiza_state, ['state'], 10)}),
    }
    _sql_constraints = [
        ('discente_ps_unique', 'unique(perfil_id,processo_seletivo_id)',
         u'Não é permitido inscrever o mesmo discente multiplas vezes em um mesmo Processo Seletivo!'),
    ]
    _constraints = [
        (lambda cls, *args, **kwargs: cls.valida_processo_seletivo(*args, **kwargs),
         u'Não é possível realizar as ações desejadas enquanto o processo seletivo for inválido',
         [u'Processo Seletivo']),
    ]

    # Métodos sobrescritos
    def name_get(self, cr, uid, ids, context=None):
        """
        === Sobrescrita do método osv.Model.search
        Define como inscrição será visualizada em campos many2one.
        """
        return [(insc.id, u"%s (Matrícula: %s)" % (insc.discente_id.name, insc.perfil_id.matricula))
                for insc in self.browse(cr, uid, ids, context=context)]

    def name_search(self, cr, uid, name='', args=None, operator='ilike', context=None, limit=100):
        """
        === Sobrescrita do método osv.Model.search
        Ao pesquisar inscrições em campos many2one, será pesquisado pelo nome do discente ou matrícula.
        """
        discentes_ids = self.pool.get("ud.employee").search(cr, uid, [("name", operator, name)], context=context)
        args += [("discente_id", "in", discentes_ids)]
        perfil_model = self.pool.get("ud.perfil")
        for perfil in perfil_model.search(cr, uid, [("matricula", "=", name)]):
            discentes_ids.append(perfil_model.browse(cr, uid, perfil, context).ud_papel_id.id)
        ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        """
        === Extensão do método osv.Model.search
        Filtra as inscrições se context tiver a chave para filtrar discente e/ou orientador. A primeira opção limita as
        inscrições ao proprietário da mesma, a segunda limita as inscrições pelas disciplinas que foram selecionadas
        na inscrição. É necessário saber que a primeira pode influenciar no resultado da segunda.
        """
        context = context or {}
        pessoa_id = None
        if context.pop("filtrar_discente", False):
            pessoa_id = get_ud_pessoa_id(self, cr, uid)
            if not pessoa_id:
                return []
            perfis = self.pool.get("ud.perfil").search(cr, SUPERUSER_ID, [("ud_papel_id", "=", pessoa_id)])
            args += [("perfil_id", "in", perfis)]
        res = super(Inscricao, self).search(cr, uid, args, offset, limit, order, context, count)
        if context.get("filtrar_orientador", False):
            if not pessoa_id:
                pessoa_id = get_ud_pessoa_id(self, cr, uid)
                if not pessoa_id:
                    return []
                perfis = self.pool.get("ud.perfil").search(cr, SUPERUSER_ID, [("ud_papel_id", "=", pessoa_id)],
                                                           context=context)
            pontuacoes_model = self.pool.get("ud_monitoria.pontuacoes_disciplina")
            pontuacoes = pontuacoes_model.search(cr, uid, [("inscricao_id", "in", res)], context=context)
            return list(
                set([pont.inscricao_id.id
                     for pont in pontuacoes_model.browse(cr, uid, pontuacoes, context)
                     if pont.disciplina_id.perfil_id.id in perfis])
            )
        return res

    # Validadores
    def valida_processo_seletivo(self, cr, uid, ids, context=None):
        """
        Verifica se o processo seletivo correspondente é inválido.
        """
        for insc in self.browse(cr, uid, ids, context=context):
            if insc.processo_seletivo_id.status in ["invalido", "demanda", "novo"]:
                return False
        return True
