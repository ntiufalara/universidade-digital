# coding: utf-8
from datetime import datetime
from openerp import SUPERUSER_ID
from openerp.osv import fields, osv, orm
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, timedelta
from ..models.util import data_hoje


class DisciplinasParaPsWizard(osv.TransientModel):
    _name = 'ud_monitoria.disciplinas_para_ps_wizard'
    _description = u'Adição de disciplinas em Processo Seletivo (UD)'

    _columns = {
        'semestre_id': fields.many2one('ud_monitoria.semestre', u"Semestre", required=True, domain=[('is_active', '=', True)]),
        'processo_seletivo_id': fields.many2one('ud_monitoria.processo_seletivo', u'Processo Seletivo', required=True,
                                                domain='[("state", "=", "demanda"), ("semestre_id", "=", semestre_id)]'),
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
    _description = u'Atribuição de permissões aos orientadores'

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

    def executar_acao(self, cr, uid, ids, context=None):
        doc_discente_model = self.pool.get('ud_monitoria.documentos_discente')
        hoje = data_hoje(self, cr, uid)
        for reverter in self.browse(cr, uid, ids, context):
            data_max = datetime.strptime(reverter.inscricao_id.write_date, DEFAULT_SERVER_DATETIME_FORMAT).date() + timedelta(30)
            if data_max < hoje:
                raise orm.except_orm(
                    u'Ação inválida!',
                    u'Não é possível modificar o status de uma inscrição modificada 30 dias atrás ou mais.'
                )
            elif not reverter.inscricao_id.disciplina_id.semestre_id.is_active:
                raise orm.except_orm(
                    u'Ação inválida!',
                    u'Não é possível alterar o status de uma incrição quando o semestre correspondente está inativo.'
                )
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

