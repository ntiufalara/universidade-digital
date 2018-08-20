# coding: utf-8
from datetime import datetime, timedelta
import logging
from re import compile

from openerp import SUPERUSER_ID
from openerp.osv import osv, fields, orm
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.translate import _

from .util import regex_regra, regex_order, regex_espacos, regex_clausula, _MESES, data_hoje, get_ud_pessoa_id

regex_hora = compile("^[0-2][0-9]:[0-5][0-9]$")
_logger = logging.getLogger('ud_monitoria')


class DocumentosDiscente(osv.Model):
    _name = 'ud_monitoria.documentos_discente'
    _description = u'Documentos de monitoria do discente (UD)'
    _order = 'state, disciplina_id'
    _STATES = [('reserva', u'Cadastro de Reserva'), ('n_bolsista', u'Colaborador(a)'),
               ('bolsista', u'Bolsista'), ('desligado', u'Desligado(a)')]

    # Métodos para campos funcionais
    def get_ch(self, cr, uid, ids, campo, args, context=None):
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

    def get_is_active(self, cr, uid, ids, campo, args, context=None):
        hoje = data_hoje(self, cr)
        res = {}
        for doc in self.browse(cr, uid, ids, context):
            res[doc.id] = (datetime.strptime(doc.disciplina_id.data_inicial, DEFAULT_SERVER_DATE_FORMAT).date() <= hoje
                          <= datetime.strptime(doc.disciplina_id.data_final, DEFAULT_SERVER_DATE_FORMAT).date())
        return res

    def update_ch(self, cr, uid, ids, context=None):
        """
        Define quais documentos deverão ter sua carga horária atualizada.
        """
        return tuple(set(
            h.documento_id.id for h in self.browse(cr, uid, ids, context)
        ))

    def update_curso_semestre(self, cr, uid, ids, context=None):
        if self._name == 'ud_monitoria.disciplina':
            return self.pool.get('ud_monitoria.documentos_discente').search(cr, uid, [('disciplina_id', 'in', ids)])
        return []

    _columns = {
        'perfil_id': fields.many2one('ud.perfil', u'Matrícula', required=True, ondelete='restrict'),
        'discente_id': fields.related('perfil_id', 'ud_papel_id', type='many2one', relation='ud.employee', readonly=True,
                                      string=u'Discente'),
        'dados_bancarios_id': fields.many2one('ud.dados.bancarios', u'Dados Bancários', ondelete='restrict',
                                              domain="[('ud_conta_id', '=', discente_id)]"),
        'disciplina_id': fields.many2one('ud_monitoria.disciplina', u'Disciplina', required=True, ondelete='restrict'),
        'tutor': fields.related('disciplina_id', 'tutoria', string=u'Tutor?', type='boolean', help=u'Indica se o discente é um tutor, caso contrário, ele é um monitor'),
        'semestre_id': fields.related('disciplina_id', 'bolsas_curso_id', 'semestre_id', type='many2one',
                                      relation='ud_monitoria.semestre', string=u'Semestre', ondelete='restrict',
                                   store={'ud_monitoria.documentos_discente': (lambda cls, cr, uid, ids, ctx: ids, ['disciplina_id'], 10),
                                          'ud_monitoria.disciplina': (update_curso_semestre, ['bolsas_curso_id'], 10)}),
        'curso_id': fields.related('disciplina_id', 'bolsas_curso_id', type='many2one', string=u'Curso',
                                   relation='ud_monitoria.bolsas_curso', ondelete='restrict',
                                   store={'ud_monitoria.documentos_discente': (lambda cls, cr, uid, ids, ctx: ids, ['disciplina_id'], 10),
                                          'ud_monitoria.disciplina': (update_curso_semestre, ['bolsas_curso_id'], 10)}
                                   ),
        'orientador_id': fields.related('disciplina_id', 'perfil_id', 'ud_papel_id', type='many2one', readonly=True,
                                        relation='ud.employee', string=u'Orientador'),
        'frequencia_ids': fields.one2many('ud_monitoria.frequencia', 'documentos_id', u'Frequências'),
        'declaracao': fields.binary(u'Declaração'),
        'certificado': fields.binary(u'Certificado'),
        'relatorio': fields.binary(u'Relatório Final'),
        'horario_ids': fields.one2many('ud_monitoria.horario', 'documento_id', u'Horários'),
        'ch': fields.function(get_ch, type='char', string=u'Carga horária', help=u'Carga horária total', store={
            'ud_monitoria.horario': (update_ch, ['hora_i', 'hora_f'], 10),
        }),
        'state': fields.selection(_STATES, u'Status', required=True),
        'is_active': fields.function(get_is_active, type='boolean', string='Ativo?'),
        # Campos de Controle
        'certificado_nome': fields.char(u'Nome Certificado'),
        'declaracao_nome': fields.char(u'Nome Declaração'),
        'relatorio_nome': fields.char(u'Nome Relatório'),
    }
    _sql_constraints = [
        ('disciplina_discente_unico', 'unique(disciplina_id,perfil_id)',
         u'Não é permitido vincular a mesma disciplina de um semestre para o mesmo discente.')
    ]
    _constraints = [
        (lambda cls, *a, **k: cls.valida_vagas(*a, **k), u'Vagas insuficientes.', [u'Disciplina']),
        (lambda cls, *a, **k: cls.valida_arquivos(*a, **k), u'Arquivo(s) inválido(s).', [u'Documentos']),
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
        res = super(DocumentosDiscente, self).create(cr, uid, vals, context)
        self.add_grupo_monitor(cr, uid, res, context)
        return res

    def unlink(self, cr, uid, ids, context=None):
        """
        === Extensão do método osv.Model.unlink
        Remove os discentes envolvidos do grupo de segurança e verifica se há algum perfil de discente como bolsista
        de monitoria para remover os dados referentes a mesma.
        """
        perfil_model = self.pool.get("ud.perfil")
        cr.execute('''
        SELECT
            DISTINCT per.id
        FROM
            %(doc)s doc INNER JOIN %(per)s per ON (doc.perfil_id = per.id)
        WHERE
            per.tipo_bolsa = 'm' AND doc.id in (%(ids)s)
            AND NOT (
                SELECT EXISTS (
                    SELECT
                        doc2.id
                    FROM
                        %(doc)s doc2 INNER JOIN %(disc)s disc ON (doc2.disciplina_id = disc.id)
                    WHERE
                        doc2.id != doc.id AND doc2.perfil_id = per.id
                        AND (disc.data_inicial <= '%(hj)s' AND disc.data_final >= '%(hj)s') = true
                )
            )
        ''' % {
            'doc': self._table,
            'per': perfil_model._table,
            'disc': self.pool.get('ud_monitoria.disciplina')._table,
            'ids': str(ids).lstrip('[(').rstrip(')],').replace('L', ''),
            'hj': data_hoje(self, cr, uid),
        })
        perfis_bolsa = [l[0] for l in cr.fetchall()]
        perfis = set()
        for doc in self.browse(cr, uid, ids, context):
            perfis.add(doc.perfil_id.id)
        super(DocumentosDiscente, self).unlink(cr, uid, ids, context)
        if perfis:
            self.remove_grupo_monitor(cr, uid, perfis=list(perfis), context=context)
        if perfis_bolsa:
            perfil_model.write(cr, SUPERUSER_ID, list(perfis),
                               {"is_bolsista": False, "perfis_bolsa": False, "valor_bolsa": False}, context)
        return True

    # Validadores
    def valida_vagas(self, cr, uid, ids, context=None):
        """
        Verifica se há vagas para novos discentes bolsistas ou colaboradores.
        """
        for doc in self.browse(cr, uid, ids, context):
            if doc.state == "bolsista":
                qtd = self.search_count(cr, uid, [
                    ('id', '!=', doc.id), ('disciplina_id', '=', doc.disciplina_id.id), ('state', '=', 'bolsista')
                ])
                if doc.disciplina_id.bolsistas <= qtd:
                    raise orm.except_orm(
                        u'Erro de Validação',
                        u'Não há vagas disponíveis para novos bolsistas.'
                    )
            elif doc.state == "n_bolsista":
                qtd = self.search_count(cr, uid, [
                    ('id', '!=', doc.id), ('disciplina_id', '=', doc.disciplina_id.id), ('state', '=', 'n_bolsista')
                ])
                if doc.disciplina_id.colaboradores <= qtd:
                    raise orm.except_orm(
                        u'Erro de Validação',
                        u'Não há vagas disponíveis para novos colaboradores.'
                    )
        return True

    def valida_arquivos(self, cr, uid, ids, context=None):
        for doc in self.browse(cr, uid, ids, context):
            if doc.relatorio_nome and not doc.relatorio_nome.endswith('.pdf'):
                raise orm.except_orm(u'Erro de Validação', u'O relatório anexado deve ser um PDF.')
            elif doc.declaracao_nome and not doc.declaracao_nome.endswith('.pdf'):
                raise orm.except_orm(u'Erro de Validação', u'A declaração anexada deve ser um PDF.')
            elif doc.certificado_nome and not doc.certificado_nome.endswith('.pdf'):
                raise orm.except_orm(u'Erro de Validação', u'O certificado anexado deve ser um PDF.')
        return True

    # Métodos de manipulação do grupo de segurança
    def add_grupo_monitor(self, cr, uid, ids, context=None):
        """
        Adiciona discente do documento ao groupo de segurança.

        :raise orm.except_orm: Se não houver um usuário vinculado ao perfil.
        """
        if isinstance(ids, (int, long)):
            ids = [ids]
        group = self.pool.get('ir.model.data').get_object(
            cr, SUPERUSER_ID, 'ud_monitoria', 'group_ud_monitoria_monitor', context
        )
        for doc in self.browse(cr, uid, ids, context):
            if not doc.discente_id.user_id:
                raise orm.except_orm(
                    u'Usuário não encontrado',
                    u'O registro no núcleo do discente "%s" não possui login de usuário.'
                    % doc.discente_id.name
                )
            group.write({'users': [(4, doc.discente_id.user_id.id)]})

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

    # Método Agendado
    def atualiza_bolsas_discente_cron(self, cr, uid, context=None):
        perfil_model = self.pool.get('ud.perfil')
        hoje = data_hoje(self, cr, uid).strftime(DEFAULT_SERVER_DATE_FORMAT)
        _logger.info(u'Removendo bolsas de monitoria/tutoria dos perfis dos discentes em disciplinas inativas.')
        cr.execute('''
        SELECT per.id
        FROM %(per)s per
        WHERE
            per.tipo_bolsa = 'm' AND per.is_bolsista = true
            AND NOT(SELECT EXISTS(
                SELECT doc.id FROM
                    %(doc)s doc INNER JOIN %(disc)s disc ON (doc.disciplina_id = disc.id)
                WHERE
                    doc.perfil_id = per.id AND disc.data_final >= '%(hj)s' AND doc.state = 'bolsista'
            ));
        ''' % {
            'doc': self.pool.get('ud_monitoria.documentos_discente')._table,
            'disc': self.pool.get('ud_monitoria.disciplina')._table,
            'per': perfil_model._table, 'hj': hoje,
        })
        ids = [l[0] for l in cr.fetchall()]
        if ids:
            perfil_model.write(cr, SUPERUSER_ID, ids, {'tipo_bolsa': False, 'is_bolsista': False, 'valor_bolsa': False})


class Horario(osv.Model):
    _name = "ud_monitoria.horario"
    _description = u"Horário do monitoria (UD)"
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

    # Validadores
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
    _name = 'ud_monitoria.frequencia'
    _description = u'Frequência do monitor/tutor (UD)'
    _order = 'state'

    _STATES = [('analise', u'Em Análise'), ('rejeitado', u'Rejeitado'), ('aceito', u'Aceito')]

    def get_disponivel(self, cr, uid, ids, campos, args, context=None):
        res = {}
        hoje = data_hoje(self, cr, uid)
        for freq in self.browse(cr, uid, ids):
            data = datetime.strptime(freq.mes_id.data_inicial, DEFAULT_SERVER_DATE_FORMAT).date()
            res[freq.id] = data <= hoje <= data + timedelta(freq.mes_id.intervalo)
        return res

    _columns = {
        'id': fields.integer(u'ID', readonly=True, invisible=True),
        'mes_id': fields.many2one('ud_monitoria.mes_frequencia', u'Mês', required=True, ondelete='cascade'),
        'frequencia': fields.binary(u'Frequência', required=True),
        'frequencia_nome': fields.char(u'Nome da Frequência'),
        'state': fields.selection(_STATES, u'Status'),
        'documentos_id': fields.many2one('ud_monitoria.documentos_discente', u'Documentos', ondelete='cascade',
                                         help=u'Documentos de um Discente', invisible=True),
        'disponivel': fields.function(get_disponivel, type='boolean', string=u'Disponível'),
    }

    _sql_constraints = [
        ('mes_doc_unico', 'unique(mes_id, documentos_id)',
         u'Não é permitido duplicar frequências para o mesmo mês, mas é possível editar caso o registro tenha sido rejeitado.')
    ]

    _constraints = [
        (lambda cls, *a, **k: cls.valida_data(*a, **k), u"Inclusão de novas frequências deve está dentro do prazo.", [u"Frequência"]),
        (lambda cls, *a, **k: cls.valida_arquivo(*a, **k), u"Arquivo inválido", [u"Frequência"]),
    ]

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = super(Frequencia, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
        if 'mes_id' in res['fields']:
            context = context or {}
            if res['fields']['mes_id']['domain']:
                domain = '{}'.format(res['fields']['mes_id']['domain'])
                domain.lstrip(' [')
                domain = '[{}, ' + domain
            else:
                domain = '[{}]'
            if context.get('semestre_id', False):
                mes_model = self.pool.get('ud_monitoria.mes_frequencia')
                hoje = data_hoje(self, cr, uid).strftime(DEFAULT_SERVER_DATE_FORMAT)
                ids = mes_model.search(cr, uid, [('semestre_id', '=', context['semestre_id']), ('data_inicial', '<=', hoje)])
                if ids:
                    ids = [
                        mes.id
                        for mes in mes_model.browse(cr, uid, ids) if mes.disponivel
                    ]
                    res['fields']['mes_id']['domain'] = domain.format(('id', 'in', ids))
            else:
                res['fields']['mes_id']['domain'] = domain.format(('id', '=', False))
        return res

    def create(self, cr, uid, vals, context=None):
        """
        === Extensão do método osv.Model.create
        Atribui o statuso ao valor "analise".
        """
        vals["state"] = "analise"
        return super(Frequencia, self).create(cr, uid, vals, context)

    def write(self, cr, uid, ids, vals, context=None):
        if 'frequencia' in vals:
            vals['state'] = 'analise'
        return super(Frequencia, self).write(cr, uid, ids, vals, context)

    # Validadores
    def valida_data(self, cr, uid, ids, context=None):
        """
        Verifica se ainda está dentro do prazo para inserção de novas frequências.
        """
        for freq in self.browse(cr, SUPERUSER_ID, ids, context):
            if not freq.mes_id.disponivel:
                return False
        return True

    def valida_arquivo(self, cr, uid, ids, context=None):
        for freq in self.browse(cr, SUPERUSER_ID, ids, context):
            if freq.frequencia_nome and not (freq.frequencia_nome.endswith('.pdf') or freq.frequencia_nome.endswith('.jpg') or freq.frequencia_nome.endswith('jpeg')):
                raise orm.except_orm(
                    u'Erro de Validação',
                    u'A frequência anexada de %s não está não é um PDF ou uma imagem JPG/JPEG.'
                    % freq.mes_id.name_get()[0][1]
                )
        return True

    # Ações de botões
    def botao_aceitar(self, cr, uid, ids, context=None):
        """
        Altera o status para "aceito".
        """
        for freq in self.browse(cr, uid, ids, context):
            args = [
                ('state', '=', 'rejeitado'), ('mes', '=', freq.mes_id.id),
            ]
            freq_ids = self.search(cr, uid, args)
            if freq_ids:
                self.unlink(cr, SUPERUSER_ID, freq_ids)
            if freq.documentos_id.orientador_id.user_id.id != uid and not self.user_has_groups(
                    cr, uid, 'ud_monitoria.group_ud_monitoria_coordenador,ud_monitoria.group_ud_monitoria_administrador'
            ):
                raise orm.except_orm(u'Permissão Negada!',
                                     u'Você não possui permissão para validar frequências desse discente')
        return self.write(cr, uid, ids, {"state": "aceito"}, context)

    def botao_rejeitar(self, cr, uid, ids, context=None):
        """
        Altera o status para "rejeitado".
        """
        for freq in self.browse(cr, uid, ids, context):
            if freq.documentos_id.orientador_id.user_id.id != uid and not self.user_has_groups(
                    cr, uid, 'ud_monitoria.group_ud_monitoria_coordenador,ud_monitoria.group_ud_monitoria_administrador'
            ):
                raise orm.except_orm(u'Permissão Negada!',
                                     u'Você não possui permissão para validar frequências desse discente')
        return self.write(cr, uid, ids, {"state": "rejeitado"}, context)
