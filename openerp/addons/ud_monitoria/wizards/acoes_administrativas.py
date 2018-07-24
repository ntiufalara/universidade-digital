# coding: utf-8
from datetime import datetime
from openerp import SUPERUSER_ID
from openerp.osv import fields, osv, orm
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, timedelta
from ..models.util import data_hoje


class DisciplinasParaPsWizard(osv.TransientModel):
    _name = 'ud_monitoria.disciplinas_para_ps_wizard'
    _description = u'Adição de disciplinas em Processo Seletivo (UD)'

    _columns = {
        'semestre_id': fields.many2one('ud_monitoria.semestre', u'Semestre', required=True, domain=[('is_active', '=', True)]),
        'processo_seletivo_id': fields.many2one('ud_monitoria.processo_seletivo', u'Processo Seletivo', required=True,
                                                domain='[("state", "in", ["demanda", "invalido"]), ("semestre_id", "=", semestre_id)]'),
        'todas': fields.boolean(u'Adicionar todas as disciplinas'),
        'bolsas_curso_id': fields.many2one('ud_monitoria.bolsas_curso', u'Curso', domain='[("semestre_id", "=", semestre_id)]'),
    }

    def default_get(self, cr, uid, fields_list, context=None):
        res = super(DisciplinasParaPsWizard, self).default_get(cr, uid, fields_list, context)
        context = context or {}
        if context.get('active_model', False) == 'ud_monitoria.semestre' and context.get('active_id', False):
            res['semestre_id'] = context['active_id']
        res['todas'] = True
        return res

    # Ação
    def adicionar(self, cr, uid, ids, context=None):
        disciplina_model = self.pool.get('ud_monitoria.disciplina')
        disciplina_ps_model = self.pool.get('ud_monitoria.disciplina_ps')
        bolsas_curso_model = self.pool.get('ud_monitoria.bolsas_curso')
        processo_seletivo_model = self.pool.get('ud_monitoria.processo_seletivo')
        sql = '''
        SELECT
            disc.id
        FROM
            %(disc)s disc INNER JOIN %(bc)s bc ON (disc.bolsas_curso_id = bc.id)
                LEFT JOIN %(disc_ps)s disc_ps ON (disc.id = disc_ps.disc_monit_id)
        WHERE
            bc.semestre_id = %(semestre_id)s
            AND (disc_ps.processo_seletivo_id is null OR disc_ps.processo_seletivo_id != %(processo_seletivo_id)s)
        '''
        for mudanca in self.browse(cr, uid, ids, context):
            cr.execute((sql + ('AND bc.id = %d' % mudanca.bolsas_curso_id.id if not mudanca.todas else '')) % {
                'disc': disciplina_model._table,
                'disc_ps': disciplina_ps_model._table,
                'bc': bolsas_curso_model._table,
                'semestre_id': mudanca.semestre_id.id,
                'processo_seletivo_id': mudanca.processo_seletivo_id.id
            })
            res = cr.fetchall()
            if res:
                processo_seletivo_model.write(cr, SUPERUSER_ID, mudanca.processo_seletivo_id.id, {
                    'disciplinas_ids': [
                        (0, 0, {'disc_monit_id': disc[0]}) for disc in res
                    ]
                })
        return True


class PermissaoOrientadoresWizard(osv.TransientModel):
    _name = 'ud_monitoria.permissao_orientador_wizard'
    _description = u'Atribuição de permissões aos orientadores (UD)'

    _columns = {
        'semestre_id': fields.many2one('ud_monitoria.semestre', u'Semestre'),
        'bolsas_curso_id': fields.many2one('ud_monitoria.bolsas_curso', u'Curso', domain='[("semestre_id", "=", semestre_id)]'),
        'pessoas': fields.text(u'Pessoas sem usuário', readonly=True),
    }

    def default_get(self, cr, uid, fields_list, context=None):
        res = super(PermissaoOrientadoresWizard, self).default_get(cr, uid, fields_list, context)
        context = context or {}
        if context.get('active_model', False) == 'ud_monitoria.semestre' and context.get('active_id', False):
            res['semestre_id'] = context['active_id']
            cr.execute('''
            SELECT
                pes.cpf, res.name, per.matricula
            FROM
                %(disc)s disc INNER JOIN %(bc)s bc ON (disc.bolsas_curso_id = bc.id)
                    INNER JOIN %(sm)s sm ON (bc.semestre_id = sm.id)
                        INNER JOIN %(per)s per ON (disc.perfil_id = per.id)
                            INNER JOIN %(pes)s pes ON (per.ud_papel_id = pes.id)
                                INNER JOIN %(res)s res ON (pes.resource_id = res.id)
            WHERE
                sm.id = %(id)s AND res.user_id is null;
            ''' % {
                'disc': self.pool.get('ud_monitoria.disciplina')._table,
                'bc': self.pool.get('ud_monitoria.bolsas_curso')._table,
                'sm': self.pool.get('ud_monitoria.semestre')._table,
                'per': self.pool.get('ud.perfil')._table,
                'pes': self.pool.get('ud.employee')._table,
                'res': self.pool.get('resource.resource')._table,
                'id': context['active_id']
            })
            lista = ''
            for l in cr.fetchall():
                lista += '- %(nome)s (CPF: %(cpf)s / SIAPE: %(siape)s)\n' % {'cpf': l[0] or '-', 'nome': l[1], 'siape': l[2]}
            res['pessoas'] = lista or False
        return res

    def adicionar(self, cr, uid, ids, context=None):
        group = self.pool.get('ir.model.data').get_object(
            cr, SUPERUSER_ID, 'ud_monitoria', 'group_ud_monitoria_orientador', context
        )
        for perms in self.browse(cr, uid, ids, context):
            complemento = ''
            if perms.bolsas_curso_id:
                complemento = ' AND bc.id = %d' % perms.bolsas_curso_id.id
            cr.execute('''
                SELECT
                    DISTINCT res.user_id
                FROM
                    %(disc)s disc INNER JOIN %(bc)s bc ON (disc.bolsas_curso_id = bc.id)
                        INNER JOIN %(sm)s sm ON (bc.semestre_id = sm.id)
                            INNER JOIN %(per)s per ON (disc.perfil_id = per.id)
                                INNER JOIN %(pes)s pes ON (per.ud_papel_id = pes.id)
                                    INNER JOIN %(res)s res ON (pes.resource_id = res.id)
                WHERE
                    sm.id = %(id)s AND res.user_id is not null%(complemento)s;
                ''' % {
                'disc': self.pool.get('ud_monitoria.disciplina')._table,
                'bc': self.pool.get('ud_monitoria.bolsas_curso')._table,
                'sm': self.pool.get('ud_monitoria.semestre')._table,
                'per': self.pool.get('ud.perfil')._table,
                'pes': self.pool.get('ud.employee')._table,
                'res': self.pool.get('resource.resource')._table,
                'id': perms.semestre_id.id,
                'complemento': complemento,
            })
            res = cr.fetchall()
            for l in res:
                group.write({'users': [(4, l[0])]})
        return True


class StatusInscricaoWizard(osv.TransientModel):
    _name = 'ud_monitoria.status_inscricao_wizard'
    _description = u'Reverte a avaliação da inscrição (UD)'
    _STATES = [('analise', u'Em Análise'), ('classificado', u'Classificado(a)'),
               ('desclassificado', u'Desclassificado(a)'), ('reserva', u'Cadastro de Reserva')]

    def _acoes_inscricao(self, cr, uid, context=None):
        context = context or {}
        if context.get('active_model', False) == 'ud_monitoria.inscricao' and context.get('active_id', False):
            inscricao = self.pool.get('ud_monitoria.inscricao').browse(cr, uid, context['active_id'], context)
            if inscricao.state == 'classificado':
                return [
                    ('analise', u'Análise'),
                    ('desclassificado', u'Desclassificado(a)'),
                    ('reserva', u'Cadastro de Reserva'),
                ]
            elif inscricao.state == 'desclassificado':
                return [
                    ('analise', u'Análise'),
                    ('classificado', u'Classificado(a)'),
                    ('reserva', u'Cadastro de Reserva'),
                ]
            elif inscricao.state == 'reserva':
                return [
                    ('analise', u'Análise'),
                    ('classificado', u'Classificado(a)'),
                    ('desclassificado', u'Desclassificado(a)'),
                ]
        return []

    _columns = {
        'inscricao_id': fields.many2one('ud_monitoria.inscricao', u'Inscrição', required=True),
        'perfil_id': fields.related('inscricao_id', 'perfil_id',  type='many2one', relation='ud.perfil', string=u'Matrícula', readonly=True),
        'discente_id': fields.related('inscricao_id', 'perfil_id', 'ud_papel_id',  type='many2one', relation='ud.employee', string=u'Discente', readonly=True),
        'bolsas_curso_id': fields.related('inscricao_id', 'bolsas_curso_id',  type='many2one', relation='ud_monitoria.bolsas_curso', string=u'Curso', readonly=True),
        'disciplina_id': fields.related('inscricao_id', 'disciplina_id',  type='many2one', relation='ud_monitoria.disciplina_ps', string=u'Disciplina(s)', readonly=True),
        'state': fields.related('inscricao_id', 'state', type='selection', selection=_STATES, string=u'Status da inscrição',
                                readonly=True),
        'acao_inscricao': fields.selection(_acoes_inscricao, u'Ação Inscricao', required=True),
        'ignorar_pontuacao': fields.boolean(u"Ignorar pontuacao"),
    }

    def default_get(self, cr, uid, fields_list, context=None):
        res = super(StatusInscricaoWizard, self).default_get(cr, uid, fields_list, context)
        context = context or {}
        if context.get('active_model', False) == 'ud_monitoria.inscricao' and context.get('active_id', False):
            res['inscricao_id'] = context['active_id']
            inscricao = self.pool.get('ud_monitoria.inscricao').browse(cr, uid, context['active_id'], context)
            res['perfil_id'] = inscricao.perfil_id.id
            res['discente_id'] = inscricao.discente_id.id
            res['bolsas_curso_id'] = inscricao.bolsas_curso_id.id
            res['disciplina_id'] = inscricao.disciplina_id.id
            res['state'] = inscricao.state
        return res

    def view_init(self, cr, uid, fields_list, context=None):
        context = context or {}
        if context.get('active_model', False) == 'ud_monitoria.inscricao' and context.get('active_id', False):
            inscricao = self.pool.get('ud_monitoria.inscricao').browse(cr, uid, context['active_id'], context)
            data_max = datetime.strptime(inscricao.write_date, DEFAULT_SERVER_DATETIME_FORMAT).date() + timedelta(30)
            if data_max < data_hoje(self, cr, uid):
                raise orm.except_orm(
                    u'Ação Indisponível!',
                    u'Inscrições modificadas há mais de 30 dias não podem ter seu status modificado'
                )
            elif not inscricao.disciplina_id.semestre_id.is_active:
                raise orm.except_orm(
                    u'Ação Indisponível!',
                    u'A modificação do status é permitidas apenas quando o semestre correspondente está ativo.'
                )

    def executar_acao(self, cr, uid, ids, context=None):
        doc_discente_model = self.pool.get('ud_monitoria.documentos_discente')
        for reverter in self.browse(cr, uid, ids, context):
            doc_discente = doc_discente_model.search(cr, uid, [
                ('perfil_id', '=', reverter.perfil_id.id),
                ('disciplina_id', '=', reverter.disciplina_id.disc_monit_id.id)
            ])
            if doc_discente:
                doc_discente_model.unlink(cr, SUPERUSER_ID, doc_discente, context)
            if reverter.acao_inscricao == 'classificado':
                reverter.inscricao_id.write({'state': 'analise'})
                if reverter.ignorar_pontuacao:
                    reverter.inscricao_id.classificar_direto()
                else:
                    reverter.inscricao_id.classificar_media()
            elif reverter.acao_inscricao == 'reserva':
                reverter.inscricao_id.write({'state': 'analise'})
                reverter.inscricao_id.cadastro_reserva()
            else:
                reverter.inscricao_id.write({'state': reverter.acao_inscricao})
        return True


class AlteracaoDatasDisciplinaWizard(osv.TransientModel):
    _name = 'ud_monitoria.alteracao_datas_disciplina_wizard'
    _description = u'Alteração de datas de disciplinas (UD)'

    _columns = {
        'semestre_id': fields.many2one('ud_monitoria.semestre', u'Semestre', required=1, domain='[("is_active", "=", True)]'),
        'todos_cursos': fields.boolean(u'Todos os cursos?', help=u'Informa se a mudança será aplicada a todos os cursos.'),
        'bolsas_curso_id': fields.many2one('ud_monitoria.bolsas_curso', u'Curso', domain='[("semestre_id", "=", semestre_id)]'),
        'todas_disciplinas': fields.boolean(u'Todas as disciplinas?',
                                            help=u'Informa se a mudança será aplicada a todas as disciplinas do curso escolhido.'),
        'disciplina_id': fields.many2one('ud_monitoria.disciplina', u'Disciplina', domain='[("bolsas_curso_id", "=", bolsas_curso_id)]'),
        'perfil_id': fields.related('disciplina_id', 'perfil_id', type='many2one', relation='ud.perfil', string=u'SIAPE', readonly=True),
        'orientador_id': fields.related('disciplina_id', 'perfil_id', 'ud_papel_id', type='many2one', relation='ud.employee', string=u'Orientador(a)', readonly=True),
        'data_inicial': fields.date(u'Data Inicial'),
        'data_final': fields.date(u'Data Final'),
        'bolsistas_ids': fields.many2many('ud.perfil', 'ud_monitoria_alter_data_per_wizard_rel', 'alterar_id',
                                          'perfil_id', u'Ex. Bolsistas'),
        'valor_bolsa': fields.float(u'Valor da bolsa', required=True, help=u'Especifica o valor da bolsa para reativação do documento dos discentes.'),
    }

    _defaults = {
        'todos_cursos': True,
        'todas_disciplinas': True,
        'valor_bolsa': 400.
    }

    def default_get(self, cr, uid, fields_list, context=None):
        res = super(AlteracaoDatasDisciplinaWizard, self).default_get(cr, uid, fields_list, context)
        context = context or {}
        if context.get('active_id', False):
            if context.get('active_model', False) == 'ud_monitoria.semestre':
                res['semestre_id'] = context['active_id']
            elif context.get('active_model', False) == 'ud_monitoria.bolsas_curso':
                bc = self.pool.get('ud_monitoria.bolsas_curso').browse(cr, uid, context['active_id'])
                res['semestre_id'] = bc.semestre_id.id
                res['bolsas_curso_id'] = bc.id
                res['todos_cursos'] = False
            elif context.get('active_model', False) == 'ud_monitoria.disciplina':
                disc = self.pool.get('ud_monitoria.disciplina').browse(cr, uid, context['active_id'])
                res['semestre_id'] = disc.bolsas_curso_id.semestre_id.id
                res['bolsas_curso_id'] = disc.bolsas_curso_id.id
                res['disciplina_id'] = disc.id
                res['perfil_id'] = disc.perfil_id.id
                res['orientador_id'] = disc.orientador_id.id
                res['data_inicial'] = disc.data_inicial
                res['data_final'] = disc.data_final
                res['todos_cursos'] = False
                res['todas_disciplinas'] = False
        return res

    def executar_sql_discente(self, cr, uid, condicao, retorno='per.id'):
        cr.execute('''
        SELECT
            DISTINCT %(retorno)s
        FROM
            "%(per)s" per INNER JOIN "%(doc)s" doc ON (per.id = doc.perfil_id)
                INNER JOIN "%(disc)s" disc ON (doc.disciplina_id = disc.id)
                    INNER JOIN "%(cur)s" cur ON (disc.bolsas_curso_id = cur.id)
        WHERE
            %(condicao)s AND doc.state = 'bolsista' AND disc.data_final < '%(hj)s'
            AND per.is_bolsista = true AND per.tipo = 'a' AND (
                per.tipo_bolsa != 'm' OR (SELECT EXISTS(
                    SELECT
                        doc2.id
                    FROM
                        "%(doc)s" doc2 INNER JOIN "%(disc)s" disc2 ON (doc2.disciplina_id = disc2.id)
                    WHERE
                        doc2.id != doc.id AND disc2.data_final >= '%(hj)s' AND doc2.perfil_id = doc.perfil_id
                        AND doc2.state = 'bolsista'
                ))
            );
            ''' % {
                'per': self.pool.get('ud.perfil')._table,
                'doc': self.pool.get('ud_monitoria.documentos_discente')._table,
                'disc': self.pool.get('ud_monitoria.disciplina')._table,
                'cur': self.pool.get('ud_monitoria.bolsas_curso')._table,
                'condicao': condicao,
                'retorno': retorno,
                'hj': data_hoje(self, cr, uid),
            })

    def onchange_semestre(self, cr, uid, ids, todo_curso, sm, curso, context=None):
        if todo_curso and sm:
            self.executar_sql_discente(cr, uid, 'cur.semestre_id = %d' % sm)
            return {'value': {'bolsas_curso_id': False, 'bolsistas_ids': [l[0] for l in cr.fetchall()]}}
        valor = {'bolsistas_ids': []}
        if curso and self.pool.get('ud_monitoria.bolsas_curso').browse(cr, uid, curso).semestre_id.id != sm:
            valor['bolsas_curso_id'] = False
        return {'value': valor}

    def onchage_curso(self, cr, uid, ids, todo_curso, toda_disc, curso, disc, context=None):
        if not todo_curso and toda_disc and curso:
            self.executar_sql_discente(cr, uid, 'cur.id = %d' % curso)
            return {'value': {'disciplina_id': False, 'bolsistas_ids': [l[0] for l in cr.fetchall()]}}
        valor = {'bolsistas_ids': []}
        if disc and self.pool.get('ud_monitoria.disciplina').browse(cr, uid, disc).bolsas_curso_id.id != curso:
            valor['disciplina_id'] = False
        return {'value': valor}

    def onchange_disciplina(self, cr, uid, ids, todo_curso, toda_disc, disc, di, df, context=None):
        if not (todo_curso or toda_disc) and disc:
            self.executar_sql_discente(cr, uid, 'disc.id = %d' % disc)
            disc = self.pool.get('ud_monitoria.disciplina').browse(cr, uid, disc)
            valores = {'perfil_id': disc.perfil_id.id, 'orientador_id': disc.orientador_id.id,
                       'bolsistas_ids': [l[0] for l in cr.fetchall()]}
            if not di:
                valores['data_inicial'] = disc.data_inicial
            if not df:
                valores['data_final'] = disc.data_final
            return {'value': valores}
        return {'value': {'bolsistas_ids': []}}

    def onchange_todo_curso(self, cr, uid, ids, todo_curso, semestre, curso, context=None):
        valor = {}
        if todo_curso:
            if semestre:
                self.executar_sql_discente(cr, uid, 'cur.semestre_id = %d' % semestre)
                valor['bolsistas_ids'] = [l[0] for l in cr.fetchall()]
            else:
                valor['bolsistas_ids'] = []
            valor['bolsas_curso_id'] = False
        elif curso and self.pool.get('ud_monitoria.bolsas_curso').browse(cr, uid, curso).semestre_id.id != semestre:
            valor['bolsas_curso_id'] = False
        return {'value': valor}

    def onchange_toda_disciplina(self, cr, uid, ids, toda_disc, curso, disc, context=None):
        valor = {}
        if toda_disc:
            if curso:
                self.executar_sql_discente(cr, uid, 'cur.id = %d' % curso)
                valor['bolsistas_ids'] = [l[0] for l in cr.fetchall()]
            else:
                valor['bolsistas_ids'] = []
            valor['disciplina_id'] = False
        elif disc and self.pool.get('ud_monitoria.disciplina').browse(cr, uid, disc).bolsas_curso_id.id != curso:
            valor['disciplina_id'] = False
        return {'value': valor}

    def executar_acao(self, cr, uid, ids, context=None):
        """
        Altera a data inicial e/ou a data final das disciplinas do semestre, curso ou uma específica realizando as
        seguintes operações:
            - Todos os discentes de uma disciplina antes inativa serão reabilitados considerando o valor informado;
            - Em caso de conflitos de bolsas, o discente passa a ser colaborador e a bolsa fica livre;
            - Disciplinas que sejam inativadas devido a atualização também remove as bolsas de seus bolsistas.
        """
        perfil_model = self.pool.get('ud.perfil')
        curso_model = self.pool.get('ud_monitoria.bolsas_curso')
        disciplina_model = self.pool.get('ud_monitoria.disciplina')
        doc_discente_model = self.pool.get('ud_monitoria.documentos_discente')
        ocorrencia_model = self.pool.get('ud_monitoria.ocorrencia')
        hoje = data_hoje(self, cr, uid)
        mensagem = u'Houve uma alteração de datas (inicial e/ou final) de %(qtd_disc)s disciplina(s). ' \
                   u'A atualização foi realizada %(modificacao)s.\n' \
                   u'%(di)s%(df)s%(disc_a_venc)s%(disc_venc)s%(discente_conflito)s%(disc_inativa)s'
        for alter in self.browse(cr, uid, ids, context):
            responsavel = self.pool.get('ud.employee').search(cr, SUPERUSER_ID, [('user_id', '=', uid)], limit=2)
            if not alter.semestre_id.is_active:
                raise orm.except_orm(u'Semestre inativo', u'Ação não permitida para semestres inativos')
            if not responsavel:
                raise orm.except_orm(
                    u'Registro Inexistente',
                    u'Não é possível realizar essa alteração enquanto seu login não estiver vinculado ao núcleo'
                )
            if len(responsavel) > 1:
                raise orm.except_orm(
                    u'Multiplos vínculos',
                    u'Não é possível realizar essa alteração enquanto seu login possuir multiplos vínculos no núcleo'
                )
            dados_msg = {
                'di': '', 'df': '', 'disc_a_venc': '', 'disc_venc': '', 'discente_conflito': '', 'disc_inativa': ''

            }
            datas = {}
            if alter.data_inicial:
                datas['data_inicial'] = alter.data_inicial
                dados_msg['di'] = u'Data Inicial: %s\n' % datetime.strptime(alter.data_inicial, DEFAULT_SERVER_DATE_FORMAT).strftime('%d-%m-%Y')
            if alter.data_final:
                datas['data_final'] = alter.data_final
                dados_msg['df'] = u'Data Final: %s\n' % datetime.strptime(alter.data_final, DEFAULT_SERVER_DATE_FORMAT).strftime('%d-%m-%Y')
            if not datas:
                continue
            if alter.todos_cursos:
                # Se for para todos os cursos, disciplinas do semestre são processadas.
                cr.execute('''
                SELECT
                    disc.id
                FROM
                    "%(disc)s" disc INNER JOIN "%(curso)s" curso ON (disc.bolsas_curso_id = curso.id)
                WHERE
                    curso.semestre_id = %(sm)s;
                ''' % {
                    'disc': disciplina_model._table,
                    'curso': curso_model._table,
                    'sm': '%d' % alter.semestre_id.id
                })
                disciplinas = [l[0] for l in cr.fetchall()]
                condicao_sql = 'cur.semestre_id = %d' % alter.semestre_id.id
                dados_msg['modificacao'] = u'em todas as disciplinas do atual semestre (%s)' % alter.semestre_id.semestre
                dados_msg['qtd_disc'] = '%d' % len(disciplinas)
            elif alter.todas_disciplinas:
                # Se for todas as disciplinas de um curso específico, essas são processadas.
                cr.execute('''
                SELECT
                    disc.id
                FROM
                    "%(disc)s" disc INNER JOIN "%(curso)s" curso ON (disc.bolsas_curso_id = curso.id)
                WHERE
                    curso.id = %(id)s;
                ''' % {
                    'disc': disciplina_model._table,
                    'curso': curso_model._table,
                    'id': '%d' % alter.bolsas_curso_id.id
                })
                disciplinas = [l[0] for l in cr.fetchall()]
                condicao_sql = 'cur.id = %d' % alter.bolsas_curso_id.id
                dados_msg['modificacao'] = u'para as disciplinas do curso de "%s"' % alter.bolsas_curso_id.curso_id.name
                dados_msg['qtd_disc'] = '%d' % len(disciplinas)
            else:
                # Se for uma disciplina específica, essa é processada.
                condicao_sql = 'disc.id = %d' % alter.disciplina_id.id
                disciplinas = alter.disciplina_id.disciplina_ids
                dados_msg['qtd_disc'] = '%d' % len(disciplinas)
                qtd = len(alter.disciplina_id.disciplina_ids)
                if qtd > 1:
                    dados_msg['qtd_disc'] = u'1 conjunto de'
                    disciplina = None
                    for d in disciplinas[:-1]:
                        if disciplina:
                            disciplina += u', "%s - %s"' % (d.codigo, d.name)
                        else:
                            disciplina = u'"%s - %s"' % (d.codigo, d.name)
                    disciplina += u' e "%s"' % disciplina[-1]
                    dados_msg['modificacao'] = u'no conjunto de disciplinas composto por %s' % disciplina
                else:
                    dados_msg['qtd_disc'] = u'1'
                    dados_msg['modificacao'] = u'na disciplina de "%s - %s"' % (disciplinas[0].codigo, disciplinas[0].name)
                dados_msg['modificacao'] += u', sob orientação de "%s" (%s)' % (
                    alter.disciplina_id.orientador_id.name, alter.disciplina_id.perfil_id.matricula
                )
                disciplinas = [alter.disciplina_id.id]
            if not disciplinas:
                continue
            if alter.data_final:
                # Busca os discentes que perderão a bolsa devido ao vencimento da disciplina com a nova data final.
                cr.execute('''
                SELECT
                    per.id
                FROM
                    "%(per)s" per INNER JOIN "%(doc)s" doc ON (per.id = doc.perfil_id)
                        INNER JOIN "%(disc)s" disc ON (doc.disciplina_id = disc.id)
                WHERE
                    per.is_bolsista = true AND per.tipo_bolsa = 'm' AND doc.state = 'bolsista'
                    AND disc.data_final >= '%(hj)s' AND disc.data_final < '%(data)s' AND disc.id in (%(ids)s);
                ''' % {
                    'per': perfil_model._table, 'doc': doc_discente_model._table, 'disc': disciplina_model._table,
                    'data': alter.data_final, 'hj': hoje.strftime(DEFAULT_SERVER_DATE_FORMAT),
                    'ids': str(disciplinas).lstrip('([').rstrip(')],').replace('L', ''),
                })
                discentes = [l[0] for l in cr.fetchall()]
                if discentes:
                    perfil_model.write(cr, SUPERUSER_ID, discentes, {
                        'is_bolsista': False, 'tipo_bolsa': False, 'valor_bolsa': False
                    })
                    qtd = len(discentes)
                    msg = '\n'.join([u'%s - %s (%s)' % (p.matricula, p.ud_papel_id.name, p.ud_cursos.name)
                                     for p in perfil_model.browse(cr, SUPERUSER_ID, discentes)])
                    if qtd > 1:
                        dados_msg['disc_a_venc'] = u'\nDurante o processo, %d discentes perderam suas bolsas devido a' \
                                                   u'finalização da data final de suas disciplinas.\n%s\n' % (qtd, msg)
                    else:
                        dados_msg['disc_a_venc'] = u'\nDurante o processo, 1 discente perdeu sua bolsa devido a' \
                                                   u'finalização da data final de sua(s) disciplina(s).\n%s\n' % msg
                # Busca os discentes que eram bolsistas de uma disciplina e agora estão com vínculo de bolsitas de outra
                # disciplina ou outro tipo de bolsa
                self.executar_sql_discente(cr, uid, condicao_sql, 'doc.id')
                discentes = [l[0] for l in cr.fetchall()]
                if discentes:
                    doc_discente_model.write(cr, uid, discentes, {'state': 'n_bolsista'})
                    msg = '\n'.join([u'%s - %s (%s)' % (p.matricula, p.ud_papel_id.name, p.ud_cursos.name)
                                     for p in perfil_model.browse(cr, SUPERUSER_ID, discentes)])
                    dados_msg['discente_conflito'] = u'Com essa atualização, foi encontrado conflito de bolsas de um ' \
                                                     u'ou mais discentes. Como consequência, esses foram realocados ' \
                                                     u'como discentes colaboradores, liberando suas bolsas.\n%s\n' % msg
            # Busca os discentes bolsistas de disciplinas "vencidas" sem vínculo de bolsas para atualizar o valor e o vínculo da bolsa
            cr.execute('''
            SELECT
                per.id
            FROM
                "%(per)s" per INNER JOIN "%(doc)s" doc ON (per.id = doc.perfil_id)
                    INNER JOIN "%(disc)s" disc ON (doc.disciplina_id = disc.id)
            WHERE
                per.is_bolsista = false AND doc.state = 'bolsista' AND disc.data_final < '%(hj)s' AND disc.id in (%(ids)s);
            ''' % {
                'per': perfil_model._table, 'doc': doc_discente_model._table,
                'disc': disciplina_model._table, 'hj': hoje.strftime(DEFAULT_SERVER_DATE_FORMAT),
                'ids': str(disciplinas).lstrip('([').rstrip(')],').replace('L', ''),
            })
            discentes = [l[0] for l in cr.fetchall()]
            if discentes:
                perfil_model.write(cr, SUPERUSER_ID, discentes, {
                    'is_bolsista': True, 'tipo_bolsa': 'm', 'valor_bolsa': ('%.2f' % alter.valor_bolsa).replace('.', ',')
                })
                msg = '\n'.join([u'%s - %s (%s)' % (p.matricula, p.ud_papel_id.name, p.ud_cursos.name)
                                 for p in perfil_model.browse(cr, SUPERUSER_ID, discentes)])
                dados_msg['disc_inativa'] = u'Os bolsistas de disciplinas inativas foram reabilitados com bolsa no ' \
                                            u'valor de R$ %s.\n%s\n' % (
                    ('%.2f' % alter.valor_bolsa).replace('.', ','), msg
                )
            disciplina_model.write(cr, uid, disciplinas, datas)
            ocorrencia_model.create(cr, uid, {
                'semestre_id': alter.semestre_id.id, 'responsavel_id': responsavel[0],
                'name': u'Mudança de datas de uma ou mais disciplinas', 'descricao': mensagem % dados_msg
            })
        return True


class AlterarOrientadorWizard(osv.TransientModel):
    _name = 'ud_monitoria.alterar_orientador_wizard'
    _description = u'Alteração de orientador de disciplinas (UD)'

    _columns = {
        'semestre_id': fields.many2one('ud_monitoria.semestre', u'Semestre', required=True, domain=[('is_active', '=', True)]),
        'bolsas_curso_id': fields.many2one('ud_monitoria.bolsas_curso', u'Curso', required=True,
                                           domain='[("semestre_id", "=", semestre_id)]'),
        'disciplina_id': fields.many2one('ud_monitoria.disciplina', u'Disciplina', required=True,
                                         domain='[("bolsas_curso_id", "=", bolsas_curso_id)]'),
        'perfil_atual_id': fields.related('disciplina_id', 'perfil_id', type='many2one', relation='ud.perfil',
                                          string=u'SIAPE', readonly=True),
        'orientador_atual_id': fields.related('disciplina_id', 'perfil_id', 'ud_papel_id', type='many2one',
                                              relation='ud.employee', string=u'Orientador', readonly=True),
        'perfil_id': fields.many2one('ud.perfil', u'SIAPE', required=True,
                                     domain='[("id", "!=", perfil_atual_id), ("tipo", "=", "p")]'),
        'orientador_id': fields.related('perfil_id', 'ud_papel_id', type='many2one', relation='ud.employee',
                                        string=u'Orientador', readonly=True),
    }
    _constraints = [
        (lambda cls, *a, **kw: cls.registros_ativos(*a, **kw), u'Todos os registros precisam está ativos', [u'Semestre/Disciplina'])
    ]

    def default_get(self, cr, uid, fields_list, context=None):
        """
        === Extensão do método osv.TransientModel.default_get
        Caso o modelo a
        """
        res = super(AlterarOrientadorWizard, self).default_get(cr, uid, fields_list, context)
        if context.get('active_id', False):
            if context.get('active_model', False) == 'ud_monitoria.semestre':
                res['semestre_id'] = context['active_id']
            elif context.get('active_model', False) == 'ud_monitoria.bolsas_curso':
                curso = self.pool.get('ud_monitoria.bolsas_curso').browse(cr, uid, context['active_id'])
                res['bolsas_curso_id'] = context['active_id']
                res['semestre_id'] = curso.semestre_id.id
            elif context.get('active_model', False) == 'ud_monitoria.disciplina':
                disc = self.pool.get('ud_monitoria.disciplina').browse(cr, uid, context['active_id'])
                res['disciplina_id'] = context['active_id']
                res['perfil_atual_id'] = disc.perfil_id.id
                res['orientador_atual_id'] = disc.orientador_id.id
                res['bolsas_curso_id'] = disc.bolsas_curso_id.id
                res['semestre_id'] = disc.bolsas_curso_id.semestre_id.id
        return res

    # def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
    #     """
    #     === Extensão do método osv.TransientModel.fields_view_get
    #     Para atender a necessidade na view, foi adicionado a opção de filtro de perfis
    #     caso o ID da disciplina tenha sido informado. Isso permitirá que a modificação seja realizada apenas para
    #     professores do mesmo curso.
    #     """
    #     context = context or {}
    #     res = super(AlterarOrientadorWizard, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
    #     if 'perfil_id' in res['fields']:
    #         if context.get('active_id', False) and context.get('active_mode', False) == 'ud_monitoria.disciplina':
    #             domain_temp = res['fields']['perfil_id'].get('domain', [])
    #             if isinstance(domain_temp, str):
    #                 domain_temp = list(eval(domain_temp))
    #             domain = []
    #             for d in domain_temp:
    #                 if d[0] not in ['id', 'ud_cursos']:
    #                     domain.append(d)
    #             del domain_temp
    #             disciplina = self.pool.get('ud_monitoria.disciplina').browse(cr, SUPERUSER_ID, context['active_id'])
    #             domain += [('id', '!=', disciplina.perfil_id.id)]
    #             res['fields']['perfil_id']['domain'] = domain
    #     return res

    # Validadores
    def registros_ativos(self, cr, uid, ids, context=None):
        """
        Verifica se tanto a disciplina quanto o semestre estão ativos.

        :return: Boolean
        """
        hoje = data_hoje(self, cr, uid)
        for alt in self.browse(cr, uid, ids, context):
            if not alt.semestre_id.is_active:
                raise orm.except_orm(
                    u'Erro de Validação',
                    u'Não é permitido mudança de orientador quando o semestre (%s) está inativo.'
                    % alt.semestre_id.semestre
                )
            data_final = datetime.strptime(alt.disciplina_id.data_final, DEFAULT_SERVER_DATE_FORMAT).date()
            if  data_final < hoje:
                raise orm.except_orm(
                    u'Erro de Validação',
                    u'Não é permitido modificar o orientador de disciplinas com prazo final vencido (%s).'
                    % data_final.strftime('%d-%m-%Y')
                )
        return True

    # Ações de atualização de valores ao modificar dados de campos
    def onchange_curso(self, cr, uid, ids, curso, disc):
        if curso and (not disc or self.pool.get('ud_monitoria.disciplina').search(cr, uid, [('id', '=', disc), ('bolsas_curso_id', '=', curso)])):
            return {}
        return {'value': {'disciplina_id': False}}

    def onchange_disciplina(self, cr, uid, ids, disc):
        if disc:
            disc = self.pool.get('ud_monitoria.disciplina').browse(cr, uid, disc)
            return {'value': {'perfil_atual_id': disc.perfil_id.id, 'orientador_atual_id': disc.orientador_id.id}}
        return {'value': {'perfil_atual_id': False, 'orientador_atual_id': False}}

    def onchange_perfil(self, cr, uid, ids, perfil_id, context=None):
        """
        Método usado para atualizar os dados do campo "orientador_id" caso "perfil_id" seja modificado.
        """
        if perfil_id:
            perfil_id = self.pool.get('ud.perfil').browse(cr, uid, perfil_id, context)
            return {'value': {'orientador_id': perfil_id.ud_papel_id.id}}
        return {'value': {'orientador_id': False}}

    # Execução de ação
    def executar_acao(self, cr, uid, ids, context=None):
        """
        Muda o orientador de uma disciplina.

        :raise orm.except_orm: Se usuário logado não tiver ou possuir múltiplos vínculos com Perfil do núcleo.
        """
        doc_ori_model = self.pool.get('ud_monitoria.documentos_orientador')
        doc_disc_model = self.pool.get('ud_monitoria.documentos_discente')
        ocorrencia_model = self.pool.get('ud_monitoria.ocorrencia')
        pessoa_model = self.pool.get('ud.employee')
        for alt in self.browse(cr, uid, ids, context):
            if not alt.semestre_id.is_active:
                raise orm.except_orm(u'Semestre Inativo', u'Não é possível realizar essa ação em semestres inativos.')
            responsavel = pessoa_model.search(cr, SUPERUSER_ID, [('user_id', '=', uid)], limit=2)
            if not responsavel:
                raise orm.except_orm(
                    u'Registro Inexistente',
                    u'Não é possível realizar essa alteração enquanto seu login não estiver vinculado ao núcleo'
                )
            if len(responsavel) > 1:
                raise orm.except_orm(
                    u'Multiplos vínculos',
                    u'Não é possível realizar essa alteração enquanto seu login possuir multiplos vínculos no núcleo'
                )

            perfil_antigo = alt.perfil_atual_id
            alt.disciplina_id.write({'perfil_id': alt.perfil_id.id})
            novo_orientador = doc_ori_model.search(
                cr, uid, [('disciplina_id', '=', alt.disciplina_id.id), ('perfil_id', '=', alt.perfil_id.id)]
            )
            if doc_disc_model.search(cr, uid, [('disciplina_id', '=', alt.disciplina_id.id)]) and not novo_orientador:
                doc_ori_model.create(cr, uid, {'disciplina_id': alt.disciplina_id.id, 'perfil_id': alt.perfil_id.id})
            if len(alt.disciplina_id.disciplina_ids) == 1:
                discs = u'da disciplina ' + alt.disciplina_id.disciplina_ids[0].name
            else:
                discs = []
                for disc in alt.disciplina_id.disciplina_ids[:-1]:
                    discs.append(u'"%s"' % disc.name)
                discs = u'das disciplinas de ' + u', '.join(discs)
                discs += u' e ' + alt.disciplina_id.disciplina_ids[-1]
            ocorrencia_model.create(cr, SUPERUSER_ID, {
                'semestre_id': alt.disciplina_id.semestre_id.id,
                'responsavel_id': responsavel[0],
                'name': u'Mudança de orientação para "%s"' % alt.bolsas_curso_id.curso_id.name,
                'envolvidos_ids': [(6, 0, [perfil_antigo.ud_papel_id.id, alt.perfil_id.ud_papel_id.id])],
                'descricao': u'Houve uma mudança de orientador(a) %(discs)s, do curso de %(curso)s. "%(ori)s" '
                             u'(SIAPE: %(siape)s) assumiu a responsabilidade que antes pertencia à "%(ori_a)s" '
                             u'(SIAPE: %(siape_a)s).' % {
                    'discs': discs, 'curso': alt.bolsas_curso_id.curso_id.name,
                    'ori_a': perfil_antigo.ud_papel_id.name, 'siape_a': perfil_antigo.matricula,
                    'ori': alt.perfil_id.ud_papel_id.name, 'siape': alt.perfil_id.matricula,
                },
            })
        return True
