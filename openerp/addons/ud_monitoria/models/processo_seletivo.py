# coding: utf-8
from datetime import datetime, timedelta
from re import finditer
from openerp import SUPERUSER_ID
from openerp.osv import fields, osv, orm
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.translate import _
from openerp.addons.ud.ud import _TIPOS_BOLSA
from util import regex_clausula, regex_espacos, regex_order, regex_regra, data_hoje, get_ud_pessoa_id


TIPOS_BOLSA = dict(_TIPOS_BOLSA)


class CriterioAvaliativo(osv.Model):
    _name = "ud_monitoria.criterio_avaliativo"
    _description = u"Critério Avaliativo das inscrições de monitoria (UD)"
    _columns = {
        "name": fields.char(u"Nome", required=True),
        "peso": fields.float(u"Peso", help=u"Peso usado para calcular a Média Ponderada"),
        "descricao": fields.text(u"Descrição"),
        "processo_seletivo_id": fields.many2one("ud_monitoria.processo_seletivo", u"Processo Seletivo",
                                                ondelete="cascade", invisible=True)
    }
    _sql_constraints = [
        ("nome_ps_unique", "UNIQUE(name,processo_seletivo_id)",
         u"Não é permitido registrar critérios avaliativos com nomes iguais em um mesmo Processo Seletivo!"),
    ]
    _constraints = [
        (lambda cls, *args, **kwargs: cls.valida_peso(*args, **kwargs),
         u"O peso do Critério Avaliativo deve ser maior que 0.", [u"Peso"])
    ]
    _defaults = {
        "peso": 1,
    }

    # Métodos sobrescritos
    def create(self, cr, uid, vals, context=None):
        """
        === Extensão do método osv.Model.create
        Torna o nome do critério maiúsculo.
        """
        if vals.get("name", False):
            vals["name"] = vals["name"].upper()
        return super(CriterioAvaliativo, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        """
        === Extensão do método osv.Model.write
        Torna o nome do critério maiúsculo.
        """
        if vals.get("name", False):
            vals["name"] = vals["name"].upper()
        return super(CriterioAvaliativo, self).write(cr, uid, ids, vals, context=context)

    # Validadores
    def valida_peso(self, cr, uid, ids, context=None):
        """
        Verifica se o peso é menor ou igual a zero.
        """
        for crit in self.browse(cr, uid, ids, context=context):
            if crit.peso <= 0:
                return False
        return True


class Anexo(osv.Model):
    _name = "ud_monitoria.anexo"
    _description = u"Anexo de monitoria (UD)"
    _order = "create_date,name asc"
    _columns = {
        "name": fields.char(u"Nome"),
        'create_date': fields.datetime(u'Data de envio', readonly=True),
        "arquivo": fields.binary(u"Arquivo", required=True, filters="*.pdf,*.png,*.jpg,*.jpeg"),
        "processo_seletivo_id": fields.many2one("ud_monitoria.processo_seletivo", u"Processo Seletivo",
                                                ondelete="cascade"),
    }

    _constraints = [
        (lambda cls, *a, **k: cls.valida_nome(*a, **k), u"Apeas arquivos PDF são pertimitos.", [])
    ]

    # Validadores
    def valida_nome(self, cr, uid, ids, context=None):
        for anexo in self.browse(cr, uid, ids, context):
            if not anexo.name.endswith(".pdf"):
                return False
        return True


class DisciplinaPS(osv.Model):
    _name = 'ud_monitoria.disciplina_ps'
    _inherits = {'ud_monitoria.disciplina': 'disc_monit_id'}
    _description = u'Vínculo entre disciplina e processo seletivo'
    _order = 'disc_monit_id'
    _columns = {
        'id': fields.integer('ID', readonly=True, invisible=True),
        'disc_monit_id': fields.many2one('ud_monitoria.disciplina', u'Disciplina(s)', required=True, ondelete='restrict'),
        'processo_seletivo_id': fields.many2one('ud_monitoria.processo_seletivo', u'Processo Seletivo', ondelete='cascade')
    }
    _sql_constraints = [
        ('disciplina_processo_seletivo_unique', 'unique(disc_monit_id, processo_seletivo_id)',
         u'Disciplinas não pode ser duplicadas em processos seletivos.')
    ]

    # Métodos sobrescritos
    def name_get(self, cr, uid, ids, context=None):
        """
        === Sobrescrita do método osv.Model.name_get
        As informações de visualização desse modelo em campos many2one será o nome da disciplina do núcleo.
        """
        res = []
        for disc in self.browse(cr, uid, ids, context=context):
            res.append((disc.id, ' / '.join(map(lambda d: '%s (%s)' % (d.name, d.codigo), disc.disciplina_ids))))
        return res

    def name_search(self, cr, uid, name='', args=None, operator='ilike', context=None, limit=100):
        """
        === Sobrescrita do método osv.Model.name_search
        Ao realizar pesquisas em campos many2one para esse modelo, os dados inseridos serão utilizados para pesquisar a
        discplina no núcleo e fazer referência com o modelo atual.
        """
        if not args:
            args = []
        elif isinstance(args, tuple):
            args = list(args)
        if name:
            condicoes = "disc.name ilike '%%%(n)s%%' OR disc.codigo ilike '%%%(n)s%%'" %  {'n': name}
            for disc in finditer('(?P<nome>\w+(?:\s+\w+)*)\s*(?:\((?P<cod>\w+)\))?', name):
                condicoes += " OR disc.name ilike '%%%s%%'" % disc.group('nome')
                if disc.group('cod'):
                    condicoes += " OR disc.codigo ilike '%%%s%%'" % disc.group('cod')

            cr.execute('''
            SELECT
                disc_ps.id
            FROM
                %(disc_ps)s disc_ps INNER JOIN  %(disc_m)s disc_m ON (disc_ps.disc_monit_id = disc_m.id)
                    INNER JOIN ud_monitoria_disciplinas_rel disc_rel ON (disc_m.id = disc_rel.disc_monitoria)
                        INNER JOIN %(disc)s disc ON (disc_rel.disciplina_ud = disc.id)
            WHERE
                %(condicoes)s;
            ''' % {
                'disc_m': self._table,
                'disc_ps': self.pool.get('ud_monitoria.disciplina_ps')._table,
                'disc': self.pool.get('ud.disciplina')._table,
                'condicoes': condicoes
            })
            args += [('id', 'in', map(lambda l: l[0], cr.fetchall()))]
        return self.name_get(cr, uid, self.search(cr, uid, args, limit=limit, context=context), context)

    #
    # def name_search(self, cr, uid, name='', args=None, operator='ilike', context=None, limit=100):
    #     if not isinstance(args, (list, tuple)):
    #         args = []
    #     args += [("disciplina_id", "in", self.pool.get("ud.disciplina").search(cr, SUPERUSER_ID, [("name", operator, name)]))]
    #     return self.name_get(cr, uid, self.search(cr, uid, args, limit=limit, context=context), context)
    #
    # def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
    #     """
    #     === Extensão do método osv.Model.search
    #     Foi adicionado a opção de filtrar as disciplinas em que o usuário logado esteja vinculado como coordenador de
    #     monitoria do curso correspondente.
    #     """
    #     if (context or {}).get("coordenador_monitoria_curso", False):
    #         pessoa_id = get_ud_pessoa_id(self, cr, uid)
    #         if not pessoa_id:
    #             return []
    #         curso_ids = self.pool.get("ud.curso").search(cr, SUPERUSER_ID, [("coord_monitoria_id", "=", pessoa_id)])
    #         curso_ids = self.pool.get('ud_monitoria.bolsas_curso').search(cr, SUPERUSER_ID,
    #                                                                       [('curso_id', 'in', curso_ids)])
    #         args = (args or []) + [("bolsas_curso_id", "in", curso_ids)]
    #     return super(DisciplinaPS, self).search(cr, uid, args, offset, limit, order, context, count)

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = super(DisciplinaPS, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
        context = context or {}
        if 'disc_monit_id' in res['fields']:
            domain = res["fields"]["disc_monit_id"].get("domain", [])
            if isinstance(domain, str):
                domain = list(eval(domain))
            if context.get('coordenador_monitoria_curso'):
                pessoa_id = get_ud_pessoa_id(self, cr, uid)
                if pessoa_id:
                    curso_ids = self.pool.get("ud.curso").search(cr, SUPERUSER_ID, [("coord_monitoria_id", "=", pessoa_id)])
                    curso_ids = self.pool.get('ud_monitoria.bolsas_curso').search(cr, SUPERUSER_ID, [('curso_id', 'in', curso_ids)])
                    domain.extend([("bolsas_curso_id", "in", curso_ids)])
            if context.get('semestre_id', False):
                domain.extend([('semestre_id', '=', context['semestre_id'])])
            res['fields']['disc_monit_id']['domain'] = domain
        return res

    # Ações após alteração de valor na view
    def onchange_disciplina_monitoria(self, cr, uid, ids, disciplina_id, context=None):
        if disciplina_id:
            disciplina = self.pool.get('ud_monitoria.disciplina').browse(cr, SUPERUSER_ID, disciplina_id)
            return {'value': {
                'bolsas_curso_id': disciplina.bolsas_curso_id.id,
                'perfil_id': disciplina.perfil_id.id,
                'orientador_id': disciplina.orientador_id.id,
                'data_inicial': disciplina.data_inicial,
                'data_final': disciplina.data_inicial,
                'semestre_id': disciplina.semestre_id.id,
                'bolsas_disponiveis': disciplina.bolsas_disponiveis,
                'bolsistas': disciplina.bolsistas,
                'colaboradores': disciplina.colaboradores,
                'disciplina_ids': [disc.id for disc in disciplina.disciplina_ids],
            }}
        return {}


class ProcessoSeletivo(osv.Model):
    _name = "ud_monitoria.processo_seletivo"
    _description = u"Processo Seletivo de Monitoria (UD)"
    # ATENÇÃO: Esse tipo de ordenação só foi possível porque os métodos "_check_qorder" e "_generate_order_by"
    # foram sobrescritos para atender as necessidades específicas desse modelo
    _order = "CASE WHEN state = 'invalido' THEN 1 " \
             "WHEN state = 'demanda' THEN 2 " \
             "WHEN state = 'andamento' THEN 3 " \
             "WHEN state = 'novo' THEN 4 " \
             "WHEN state = 'encerrado' THEN 5 " \
             "ELSE 10 " \
             "END Asc, name asc"
    _STATES = [("invalido", u"Inválido"), ("demanda", u"Demanda disponível"), ("novo", u"Novo"),
               ("andamento", u"Em Andamento"), ("encerrado", u"Encerrado")]

    # Métodos para campos calculados
    def status(self, cr, uid, ids, campo, args, context=None):
        """
        Define o valor do status.
        """
        res = {}.fromkeys(ids, False)
        hoje = data_hoje(self, cr, uid)
        for ps in self.browse(cr, uid, ids, context):
            if hoje <= datetime.strptime(ps.prazo_demanda, DEFAULT_SERVER_DATE_FORMAT).date():
                res[ps.id] = "demanda"
            elif ps.disciplinas_ids and ps.anexos_ids:
                if hoje < datetime.strptime(ps.data_inicio, DEFAULT_SERVER_DATE_FORMAT).date():
                    res[ps.id] = "novo"
                elif hoje <= datetime.strptime(ps.data_fim, DEFAULT_SERVER_DATE_FORMAT).date():
                    res[ps.id] = "andamento"
                else:
                    res[ps.id] = "encerrado"
            else:
                res[ps.id] = "invalido"
        return res

    def atualiza_status(self, cr, uid, ids, context=None):
        """
        Gatilho utilizado para atualizar o status do processo seletivo quando os campos de disciplinas, anexos e todas
        as suas datas forem modificados.
        """
        context = context or {}
        if 'tz' not in context:
            context['tz'] = u'America/Maceio'
        hoje = data_hoje(self, cr, uid).strftime(DEFAULT_SERVER_DATE_FORMAT)
        args = [
            '&', ('id', 'in', ids), '|', '|', '|', '|', ('state', 'in', [None, 'invalido']),
            '&', ('state', '!=', 'demanda'), ('prazo_demanda', '>=', hoje),
            '&', ('state', '!=', 'novo'), '&', ('prazo_demanda', '<', hoje), ('data_inicio', '>', hoje),
            '&', ('state', '!=', 'andamento'), '&', ('data_inicio', '<=', hoje), ("data_fim", ">=", hoje),
            '&', ('state', '!=', 'encerrado'), ('data_fim', '<', hoje)
        ]
        res = self.pool.get("ud_monitoria.processo_seletivo").search(
            cr, uid, args, context=context
        )
        for ps in self.pool.get("ud_monitoria.processo_seletivo").browse(cr, uid, list(set(ids).difference(res)), context):
            if not (ps.anexos_ids and ps.disciplinas_ids):
                res.append(ps.id)
        return res

    _columns = {
        "id": fields.integer(u"ID", readonly=True, invisible=True),
        "name": fields.char(u"Nome", required=True),
        "prazo_demanda": fields.date(u"Em demanda até", required=True, help=u"Prazo final da demanda"),
        "data_inicio": fields.date(u"Data Inicial", required=True, help=u"Início das inscrições"),
        "data_fim": fields.date(u"Data Final", required=True, help=u"Encerramento das inscrições"),
        "valor_bolsa": fields.float(u"Bolsa (R$)", required=True, help=u"Valor da bolsa"),
        "tipo_media": fields.selection([("a", u"Aritmética"), ("p", u"Ponderada")], u"Tipo de Média", required=True,
                                       help=u"Tipo de média a ser utilizada na aprovação."),
        "media_minima": fields.float(u"Nota Minima", required=True, help=u"Média mínima para aprovação de discentes."),
        "state": fields.function(
            status, string=u"Status", type="selection", selection=_STATES,
            store={"ud_monitoria.processo_seletivo": (
                atualiza_status, ["prazo_demanda", "data_inicio", "data_fim", "disciplinas_ids", "anexos_ids"], 10
            )}
        ),
        "semestre_id": fields.many2one("ud_monitoria.semestre", u"Semestre", required=True, ondelete="cascade",
                                       domain=[("is_active", "=", True)], help=u"Semestres ativos"),
        "disciplinas_ids": fields.one2many("ud_monitoria.disciplina_ps", "processo_seletivo_id", u"Disciplinas"),
        "anexos_ids": fields.one2many("ud_monitoria.anexo", "processo_seletivo_id", u"Anexos"),
        "inscricoes_ids": fields.one2many("ud_monitoria.inscricao", "processo_seletivo_id", u"Inscrições"),
        "criterios_avaliativos_ids": fields.one2many("ud_monitoria.criterio_avaliativo", "processo_seletivo_id",
                                                     u"Critérios Avaliativos"),
    }
    _sql_constraints = [
        ("nome_ps_semestre_unique", "unique(name,semestre_id)",
         u"Não é permitido criar processos seletivos com mesmo nome para o mesmo semestre")
    ]
    _constraints = [
        (lambda cls, *args, **kwargs: cls.valida_datas(*args, **kwargs),
         u"Prazo de demanda deve ocorrer antes da data inicial que por sua vez deve ocorrer antes da data final.",
         [u"Prazo de Demanda, Data Inicial e/ou Data Final"]),
        (lambda cls, *args, **kwargs: cls.valida_bolsa(*args, **kwargs),
         u"O valor da bolsa não pode ser menor que 1.", [u"Bolsa"]),
        (lambda cls, *args, **kwargs: cls.valida_criterios_avaliativos(*args, **kwargs),
         u"Deve ser definido ao menos 1 critério avaliativo", [u"Critérios Avaliativos"]),
    ]
    _defaults = {
        "valor_bolsa": 400.,
        "media_minima": 7.0,
        "tipo_media": "p",
        "criterios_avaliativos_ids": [
            (0, 0, {"name": u"PROVA ESCRITA", "peso": 3}),
            (0, 0, {"name": u"MÉDIA FINAL NAS DISCIPLINAS", "peso": 3}),
            (0, 0, {"name": u"COEFICIENTE DE RENDIMENTO ACUMULADO", "peso": 2}),
            (0, 0, {"name": u"ENTREVISTA", "peso": 2}),
        ]
    }

    # Métodos Sobrescritos
    def create(self, cr, uid, vals, context=None):
        """
        === Extensão do método osv.Model.create
        Deixa o nome do processo seletivo em maiúsculo.
        """
        if "name" in vals:
            vals["name"] = vals.get("name").upper()
        return super(ProcessoSeletivo, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        """
        === Extensão do método osv.Model.write
        Impede a antecipação da data de encerramento do processo seletivo caso ele esteja em andamento ou encerrado e
        adiamento da data final para uma data anterior a atual.

        :raise orm.except_orm: Caso haja a tentantiva de alterar para um semestre inativo ou tentativa indevida de
                               antecipação ou adiamento da data de encerramento.
        """
        if "semestre_id" in vals:
            if self.pool.get("ud_monitoria.semestre").search_count(
                    cr, SUPERUSER_ID, [("id", "=", vals["semestre_id"]), ("is_active", "=", False)]):
                raise osv.except_osv(u"Registro Inativo",
                                     u"Não é permitido alterar o semestre do processo seletivo para um inativo")
        if "name" in vals:
            vals["name"] = vals.get("name").upper()
        if "data_fim" in vals:
            data_fim = vals["data_fim"]
            for ps in self.browse(cr, uid, ids, context):
                if ps.state in ["andamento", "encerrado"]:
                    if data_fim < ps.data_fim:
                        raise orm.except_orm(
                            u"Data Final",
                            u"Não é permitido antecipar a data de finalização quando o processo seletivo já está em "
                            u"andamento ou encerrado.")
                    elif ps.state == 'encerrado' and (datetime.strptime(ps.data_fim, DEFAULT_SERVER_DATE_FORMAT).date() + timedelta(7)) < data_hoje(self, cr, uid):
                        raise orm.except_orm(
                            u'Data Final',
                            u'Fora do prazo de 7 dias, após o encerramento, para reabertura do processo seletivo.'
                        )
                    elif datetime.strptime(data_fim, DEFAULT_SERVER_DATE_FORMAT).date() < datetime.utcnow().date():
                        raise osv.except_osv(u"Data Final", u"A data final do processo seletivo deve ser maior ou "
                                                            u"igual a data atual.")
        return super(ProcessoSeletivo, self).write(cr, uid, ids, vals, context=context)

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        """
        === Extensão do método osv.Model.search
        Limita os processos seletivos de acordo com seu status caso o usuário não pertença aos grupos de segurança de
        coordenador de monitoria (não é o mesmo que coordenador de monitoria do curso) e administrador.
        """
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
        """
        === Extensão do método osv.Model.default_get
        Campo semestre com valor padrão se existir em context.
        """
        res = super(ProcessoSeletivo, self).default_get(cr, uid, fields_list, context)
        res["semestre_id"] = (context or {}).get("semestre_id", False)
        return res

    def _check_qorder(self, word):
        """
        === Sobrescrita do método osv.Model._check_qorder
        Adaptação para as novas modificações da validação da cláusula de ordenação condicional.
        """
        if not regex_order.match(word):
            raise orm.except_orm(_('AccessError'),
                                 u"A ordenação do Processo Seletivo não está de acordo com o padrão. Use apenas o nome do campo ou um conjunto de casos seguidos, ou não, de ASC/DESC!")
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
            res = super(ProcessoSeletivo, self)._generate_order_by(",".join(outros), query)
            if ord_elementos:
                clausulas = ",".join(ord_elementos)
            if clausulas or res:
                clausulas = " ORDER BY " + ",".join([(clausulas or ""), (res and res[10:] or "")]).strip(",")
        return clausulas or ''

    # Validadores
    def valida_datas(self, cr, uid, ids, context=None):
        """
        Verifica se as datas de demana, data inicia e final ocorrem uma antes da outra nessa ordem.
        """
        for ps in self.browse(cr, uid, ids, context=context):
            data_inicial = datetime.strptime(ps.data_inicio, DEFAULT_SERVER_DATE_FORMAT)
            data_final = datetime.strptime(ps.data_fim, DEFAULT_SERVER_DATE_FORMAT)
            prazo_demanda = datetime.strptime(ps.prazo_demanda, DEFAULT_SERVER_DATE_FORMAT)
            if not (prazo_demanda < data_inicial < data_final):
                return False
        return True

    def valida_bolsa(self, cr, uid, ids, context=None):
        """
        Verifica se o valor da nolsa é menor que 1.
        """
        for ps in self.browse(cr, uid, ids, context=context):
            if ps.valor_bolsa < 1:
                return False
        return True

    def valida_criterios_avaliativos(self, cr, uid, ids, context=None):
        """
        Verifica se há ao menos um critério avaliativo vinculado ao processo seletivo.
        """
        for ps in self.browse(cr, uid, ids, context):
            if len(ps.criterios_avaliativos_ids) == 0:
                return False
        return True

    # Método agendado para ser executado periodicamente (ir.cron)
    def atualiza_status_cron(self, cr, uid, *args, **kwargs):
        """
        Atualiza o status dos processos seletivos para demanda, novo e andamento de acordo com suas datas utilizado o
        modelo "ir.cron".
        """
        sql = "UPDATE " + self._table + " SET state='%(status)s' WHERE state NOT IN ('invalido', '%(status)s') AND %(condicao)s;"
        hoje = data_hoje(self, cr, uid).strftime(DEFAULT_SERVER_DATE_FORMAT)
        cr.execute(sql % {'status': 'demanda', 'condicao': "prazo_demanda >= '%s'" % hoje})
        cr.execute(sql % {'status': 'novo', 'condicao': "prazo_demanda < '%(hj)s' AND data_inicio > '%(hj)s'" % {'hj': hoje}})
        cr.execute(sql % {'status': 'andamento', 'condicao': "data_inicio <= '%(hj)s' AND data_fim >= '%(hj)s'" % {'hj': hoje}})
        cr.execute(sql % {'status': 'encerrado', 'condicao': "data_fim < '%(hj)s'" % {'hj': hoje}})
        return True
