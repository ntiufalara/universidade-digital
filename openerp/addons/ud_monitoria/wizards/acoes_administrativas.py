# coding: utf-8
from openerp import SUPERUSER_ID
from openerp.osv import fields, osv


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
        for mudanca in self.browse(cr, uid, ids, context):
            cr.execute(('''
            SELECT
                disc.id
            FROM
                %(disc)s disc INNER JOIN %(bc)s bc ON (disc.bolsas_curso_id = bc.id)
                    LEFT JOIN %(disc_ps)s disc_ps ON (disc.id = disc_ps.disc_monit_id)
            WHERE
                bc.semestre_id = %(semestre_id)s
                AND (disc_ps.processo_seletivo_id is null OR disc_ps.processo_seletivo_id != %(processo_seletivo_id)s)
            ''' + ('AND bc.id = %d' % mudanca.bolsas_curso_id.id if not mudanca.todas else '')) % {
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