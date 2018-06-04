# coding: utf-8
from datetime import datetime

from openerp import SUPERUSER_ID
from openerp.osv import fields, osv
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from util import get_ud_pessoa_id, data_hoje


class Curso(osv.Model):
    _name = "ud.curso"
    _description = u"Extensão de Curso (UD)"
    _inherit = "ud.curso"
    _columns = {
        "coord_monitoria_id": fields.many2one("ud.employee", u"Coordenador de Monitoria"),
    }
    _sql_constraints = [
        ("coord_monitoria_unico", "unique(coord_monitoria_id)",
         u"Uma pessoa pode ser coordenador de monitoria de apenas 1 curso."),
    ]

    # Métodos sobrescritos
    def create(self, cr, uid, vals, context=None):
        """
        === Extensão do método osv.Model.create
        Verifica se foi vinculado alguém como coordenador de monitoria de um curso para adicioná-lo ao grupo de segurança
        correspondente.
        """
        res = super(Curso, self).create(cr, uid, vals, context)
        if vals.get("coord_monitoria_id", False):
            group = self.pool.get("ir.model.data").get_object(
                cr, SUPERUSER_ID, "ud_monitoria", "group_ud_monitoria_coord_disciplina", context
            )
            usuario = self.pool.get("ud.employee").browse(cr, uid, vals["coord_monitoria_id"], context).user_id
            if usuario:
                group.write({"users": [(4, usuario.id)]})
        return res

    def write(self, cr, uid, ids, vals, context=None):
        """
        === Extensão do método osv.Model.write
        Verifica a alteração do coordenador de monitoria de um curso. Se adicionado, esse será inserido no grupo de
        segurança correspodente. Se modificado, o anterior e retirado do grupo de segurança e o novo é adicionado. Se
        o orientador é retirado, então também é removido do grupo de segurança.

        :attention: Antes de remover qualquer orientador do grupo de segurança, é verificado se esse não possui nenhum
        vínculo com outros cursos.
        """
        if "coord_monitoria_id" in vals:
            coordenadores_antigos = []
            for curso in self.browse(cr, uid, ids, context):
                if curso.coord_monitoria_id.user_id:
                    coordenadores_antigos.append(curso.coord_monitoria_id)
            super(Curso, self).write(cr, uid, ids, vals, context)
            group = self.pool.get("ir.model.data").get_object(
                cr, SUPERUSER_ID, "ud_monitoria", "group_ud_monitoria_coord_disciplina", context
            )
            if vals.get("coord_monitoria_id", False):
                user = self.pool.get("ud.employee").browse(cr, uid, vals["coord_monitoria_id"], context)
                if user.user_id:
                    user = user.user_id.id
                    group.write({"users": [(4, user)]})
                    for coord in coordenadores_antigos:
                        if coord.user_id:
                            if (coord.user_id.id != user and self.search_count(
                                    cr, uid, [("coord_monitoria_id", "=", coord.id)]) == 0):
                                group.write({"users": [(3, coord.user_id.id)]})
            else:
                for coord in coordenadores_antigos:
                    if coord.user_id:
                        if self.search_count(cr, uid, [("coord_monitoria_id", "=", coord.id)]) == 0:
                            group.write({"users": [(3, coord.user_id.id)]})
            return True
        return super(Curso, self).write(cr, uid, ids, vals, context)

    def unlink(self, cr, uid, ids, context=None):
        """
        === Extensão do método osv.Model.unlink
        Virifica se o coordenador de monitoria do curso não possui vínculos com outras disciplinas para essa função e
        remove-o do grupo de segurança correspondente.
        """
        coordenadores = [curso.coord_monitoria_id for curso in self.browse(cr, uid, ids, context)]
        super(Curso, self).unlink(cr, uid, ids, context)
        group = self.pool.get("ir.model.data").get_object(
            cr, SUPERUSER_ID, "ud_monitoria", "group_ud_monitoria_coord_disciplina", context
        )
        for coordenador in coordenadores:
            if self.search_count(cr, uid, [("coord_monitoria_id", "=", coordenador.id)]) == 0:
                if coordenador.user_id:
                    group.write({"users": [(3, coordenador.user_id.id)]})
        return True


class DisciplinaMonitoria(osv.Model):
    _name = 'ud_monitoria.disciplina'
    _description = u'Disciplinas de monitoria (UD)'
    _order = 'disciplina_id'

    # Métodos para campos funcionais
    def get_dados_bolsas(self, cr, uid, ids, campo, args, context=None):
        """
        Calcula o número de bolsas utilizadas e disponiveis para uso.

        :return: {ID_MODELO: {'disponiveis': QTD_BOLSAS_DISPONIVEIS, 'utilizadas': QTD_BOLSAS_UTILIZADAS}}
        """
        res = {}
        doc_discente = self.pool.get('ud_monitoria.documentos_discente')
        hoje = data_hoje(self, cr).strftime(DEFAULT_SERVER_DATE_FORMAT)
        for disc in self.browse(cr, uid, ids, context):
            cr.execute('''
            SELECT
                COUNT(doc.id)
            FROM
                %(doc)s doc INNER JOIN %(disc)s disc ON (doc.disciplina_id = disc.id)
            WHERE
                (disc.data_inicial <= '%(hj)s' AND disc.data_final >= '%(hj)s') = true
                AND doc.state = 'bolsista'
            ''' % {
                'doc': doc_discente._table,
                'disc': self._table,
                'hj': hoje
            })
            utilizadas = cr.fetchone()[0]
            res[disc.id] = {
                'bolsas_disponiveis': disc.bolsas - utilizadas,
                'bolsas_utilizadas': utilizadas,
            }
        return res

    def get_discentes(self, cr, uid, ids, campo, args, context=None):
        """
        Busca todos os discentes e separa-os em um dicionário de acordo com seu status e seu campo correspondente.
        """
        doc_model = self.pool.get("ud_monitoria.documentos_discente")
        res = {}
        for disc_id in ids:
            res[disc_id] = {
                "bolsista_ids": doc_model.search(cr, SUPERUSER_ID, [("disciplina_id", "=", disc_id), ("state", "=", "bolsista")], context=context),
                "n_bolsista_ids": doc_model.search(cr, SUPERUSER_ID, [("disciplina_id", "=", disc_id), ("state", "=", "n_bolsista")], context=context),
                "reserva_ids": doc_model.search(cr, SUPERUSER_ID, [("disciplina_id", "=", disc_id), ("state", "=", "reserva")], context=context),
                "desligado_ids": doc_model.search(cr, SUPERUSER_ID, [("disciplina_id", "=", disc_id), ("state", "=", "desligado")], context=context),
            }
        return res

    def get_is_active(self, cr, uid, ids, campo, args, context=None):
        res = {}
        hoje = data_hoje(self, cr)
        for disc in self.browse(cr, uid, ids, context):
            res[disc.id] = datetime.strptime(disc.data_inicial, DEFAULT_SERVER_DATE_FORMAT).date() <= hoje <= datetime.strptime(disc.data_final, DEFAULT_SERVER_DATE_FORMAT).date()
        return res

    def update_bolsas_utilizadas(self, cr, uid, ids, context=None):
        """
        Busca os ids de BolsasDisciplinas quando o campo state de DocumentosDiscente é atualizado, não é igual a
        'reserva' e o semestre correspondente está ativo.

        :return: Lista de ids de Bolsas de Disciplinas a serem atualizadas.
        """
        if self._name == 'ud_monitoria.disciplina' or not ids:
            return ids
        disc_model = self.pool.get('ud_monitoria.disciplina')
        dd_model = self.pool.get('ud_monitoria.documentos_discente')
        sm_model = self.pool.get('ud_monitoria.semestre')
        bc_model = self.pool.get('ud_monitoria.bolsas_curso')
        sql = '''
        SELECT
            disc.id
        FROM
            %(disc)s disc
            INNER JOIN %(doc)s doc ON (disc.id = doc.disciplina_id)
                INNER JOIN %(bc)s bc ON (disc.bolsas_curso_id = bc.id)
                    INNER JOIN %(sm)s sm ON (bc.semestre_id = sm.id)
        WHERE
            sm.is_active = true AND doc.id in (%(ids)s) AND doc.state != 'reserva';
        ''' % {
            'disc': disc_model._table, 'doc': dd_model._table, 'sm': sm_model._table, 'bc': bc_model._table,
            'ids': str(ids).lstrip('([').rstrip(')],').replace('L', '')
        }
        cr.execute(sql)
        res = cr.fetchall()
        if res:
            return [linha[0] for linha in res]
        return []

    _columns = {
        'id': fields.integer('ID', readonly=True, invisible=True),
        'bolsas_curso_id': fields.many2one('ud_monitoria.bolsas_curso', u'Curso', required=True, ondelete='cascade'),
        'semestre_id': fields.related('bolsas_curso_id', 'semestre_id', type='many2one', string=u'Semestre',
                                      relation='ud_monitoria.semestre', readonly=True),
        'disciplina_id': fields.many2one('ud.disciplina', u'Disciplina', required=True, ondelete='restrict'),
        'bolsas': fields.integer(u'Bolsas', required=True, help=u'Número de bolsas distribuídas'),
        'bolsas_utilizadas': fields.function(
            get_dados_bolsas, type='integer', string=u'Bolsas utilizadas', multi='bolsas_disciplina_monitoria',
            store={
                'ud_monitoria.documentos_discente': (update_bolsas_utilizadas, ['state'], 9),
                'ud_monitoria.disciplina': (lambda cls, cr, uid, ids, ctx=None: ids, ['bolsas'], 9),
            }
        ),
        'bolsas_disponiveis': fields.function(
            get_dados_bolsas, type='integer', string=u'Bolsas disponíveis', multi='bolsas_disciplina_monitoria',
            store={
                'ud_monitoria.documentos_discente': (update_bolsas_utilizadas, ['state'], 9),
                'ud_monitoria.disciplina': (lambda cls, cr, uid, ids, ctx=None: ids, ['bolsas'], 9),
            }
        ),
        'monitor_s_bolsa': fields.integer(u'Vagas sem bolsa (Monitor)', required=True),
        'tutor_s_bolsa': fields.integer(u'Vagas sem bolsa (Tutor)', required=True),
        'data_inicial': fields.date(u'Data Inicial', required=True),
        'data_final': fields.date(u'Data Final', required=True),
        'is_active': fields.function(get_is_active, type='boolean', string=u'Ativo'),
        'orientador_ids': fields.one2many('ud_monitoria.documentos_orientador', 'disciplina_id', u'Orientadores'),
        "bolsista_ids": fields.function(get_discentes, type="many2many", relation="ud_monitoria.documentos_discente",
                                        string=u"Bolsistas", multi="disciplina_monitoria_discentes"),
        "n_bolsista_ids": fields.function(get_discentes, type="many2many", relation="ud_monitoria.documentos_discente",
                                          string=u"Não Bolsistas", multi="disciplina_monitoria_discentes"),
        "reserva_ids": fields.function(get_discentes, type="many2many", relation="ud_monitoria.documentos_discente",
                                       string=u"Cadastro de Reserva", multi="disciplina_monitoria_discentes"),
        "desligado_ids": fields.function(get_discentes, type="many2many", relation="ud_monitoria.documentos_discente",
                                         string=u"Cadastro de Reserva", multi="disciplina_monitoria_discentes"),

    }
    _constraints = [
        (lambda cls, *args, **kwargs: cls.valida_datas(*args, **kwargs),
         u'A data inicial deve ocorrer antes da data final.', [u'Data inicial e Data final']),
        (lambda cls, *args, **kwargs: cls.valida_bolsas(*args, **kwargs),
         u'O total de bolsas das disciplinas não pode ultrapassar a quatidade máxima definida em seu curso.', [u'Bolsas']),
        (lambda cls, *args, **kwargs: cls.valida_bolsas_utilizadas(*args, **kwargs),
         u'O número de bolsas não pode ser menor que o número de bolsas utilizadas.', [u'Bolsas utilizadas']),
        (lambda cls, *args, **kwargs: cls.valida_disciplina(*args, **kwargs),
         u'A disciplina deve pertencer ao curso selecionado.', [u'Disciplina']),
        (lambda cls, *args, **kwargs: cls.valida_valor_negativo(*args, **kwargs),
         u'Valor negativo não é permitido em bolsas, vagas de tutores e monitores.', [u'Bolsas e Vagas (Monitor/Tutor)']),
        (lambda cls, *args, **kwargs: cls.valida_orientadores(*args, **kwargs),
         u'Deve ser definido ao menos um orientador para a disciplina.', [u'Orientadores']),
    ]
    _sql_constraints = [
        ('bolsas_curso_disciplina_unique', 'unique(bolsas_curso_id, disciplina_id)',
         u'Não é permitido duplicar disciplinas.')
    ]

    # Métodos sobrescritos
    def name_get(self, cr, uid, ids, context=None):
        """
        === Sobrescrita do método osv.Model.name_get
        As informações de visualização desse modelo em campos many2one será o nome da disciplina do núcleo.
        """
        return [(disc.id, '%s (%s)' % (disc.disciplina_id.name, disc.disciplina_id.codigo)) for disc in
                self.browse(cr, uid, ids, context=context)]

    def name_search(self, cr, uid, name='', args=None, operator='ilike', context=None, limit=100):
        """
        === Sobrescrita do método osv.Model.name_search
        Ao realizar pesquisas em campos many2one para esse modelo, os dados inseridos serão utilizados para pesquisar a
        discplina no núcleo e fazer referência com o modelo atual.
        """
        if not isinstance(args, (list, tuple)):
            args = []
        if not (name == '' and operator == 'ilike'):
            args += [("disciplina_id", "in", self.pool.get("ud.disciplina").search(
                cr, SUPERUSER_ID, ['|', ("name", operator, name), ('codigo', operator, name)]
            ))]
        return self.name_get(cr, uid, self.search(cr, uid, args, limit=limit, context=context), context)

    def default_get(self, cr, uid, fields_list, context=None):
        """
        === Extensão do método osv.Model.default_get
        Adiciona um curso padrão no campo correspondente quando disciplina for criada por usando o filtro de coordenador
        de monitoria de algum curso.
        """
        context = context or {}
        res = super(DisciplinaMonitoria, self).default_get(cr, uid, fields_list, context)
        if context.get("coordenador_monitoria_curso", False):
            if not context.get("semestre_id", False):
                return res
            pessoa_id = get_ud_pessoa_id(self, cr, uid)
            if pessoa_id:
                curso_ids = self.pool.get("ud.curso").search(cr, SUPERUSER_ID, [("coord_monitoria_id", "=", pessoa_id)],
                                                             context=context)
                if not curso_ids:
                    return res
                curso_ids = self.pool.get('ud_monitoria.bolsas_curso').search(
                    cr, SUPERUSER_ID, [('semestre_id', '=', context["semestre_id"]), ('curso_id', 'in', curso_ids)],
                    context=context
                )
                if not curso_ids:
                    return res
                res["bolsas_curso_id"] = curso_ids[0]
        return res

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        """
        === Extensão do método osv.Model.fields_view_get
        Define o filtro de cursos com de acordo com os que estão listados nas configurações do semestre para definir
        quantas bolsas cada um possui. Caso seja definido para filtrar pelo coordenador do curso de monitoria usando
        o marcador em context, essa lista, já filtrada, será limitada aos cursos que o usuário logado é o coordenador
        de monitoria.
        """
        context = context or {}
        res = super(DisciplinaMonitoria, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
        if 'bolsas_curso_id' in res["fields"]:
            domain_temp = res["fields"]["bolsas_curso_id"].get("domain", [])
            if isinstance(domain_temp, str):
                domain_temp = list(eval(domain_temp))
            domain = []
            for d in domain_temp:
                if d[0] != "id":
                    domain.append(d)
            del domain_temp
            if context.get("semestre_id", None):
                domain.append(('semestre_id', '=', context['semestre_id']))
                if context.get('coordenador_monitoria_curso', False):
                    domain.append(('curso_id', 'in', self.pool.get('ud.curso').search(
                        cr, uid, [("coord_monitoria_id", "=", get_ud_pessoa_id(self, cr, uid))]
                    )))
            res["fields"]["bolsas_curso_id"]["domain"] = domain
        if 'curso_id' in context and 'disciplina_id' in res['fields']:
            domain_temp = res["fields"]["disciplina_id"].get("domain", [])
            if isinstance(domain_temp, str):
                domain_temp = list(eval(domain_temp))
            domain = []
            for d in domain_temp:
                if d[0] != "id":
                    domain.append(d)
            del domain_temp
            res["fields"]["disciplina_id"]['domain'] = domain + [
                ('id', 'in', self.pool.get('ud.disciplina').search(cr, SUPERUSER_ID, [('ud_disc_id', '=', context['curso_id'])]))
            ]
        return res

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        """
        === Extensão do método osv.Model.search
        Foi adicionado a opção de filtrar as disciplinas em que o usuário logado esteja vinculado como coordenador de
        monitoria do curso correspondente.
        """
        if (context or {}).get("coordenador_monitoria_curso", False):
            pessoa_id = get_ud_pessoa_id(self, cr, uid)
            if not pessoa_id:
                return []
            curso_ids = self.pool.get("ud.curso").search(cr, SUPERUSER_ID, [("coord_monitoria_id", "=", pessoa_id)])
            curso_ids = self.pool.get('ud_monitoria.bolsas_curso').search(cr, SUPERUSER_ID,
                                                                          [('curso_id', 'in', curso_ids)])
            args = (args or []) + [("bolsas_curso_id", "in", curso_ids)]
        if (context or {}).get("disciplina_ativa", False):
            hoje = data_hoje(self, cr).strftime(DEFAULT_SERVER_DATE_FORMAT)
            args = (args or []) + [('data_inicial', '<=', hoje), ('data_final', '>=', hoje)]
        return super(DisciplinaMonitoria, self).search(cr, uid, args, offset, limit, order, context, count)

    def unlink(self, cr, uid, ids, context=None):
        ids = ids if isinstance(ids, (list, tuple)) else [ids]
        cr.execute('''
        SELECT EXISTS(
            SELECT
                doc.id
            FROM
                %(doc)s doc INNER JOIN %(disc)s disc ON (doc.disciplina_id = disc.id)
            WHERE
                disc.id in (%(ids)s)
                AND (doc.declaracao is not null OR doc.certificado is not null)
        );
        ''' % {
            'doc': self.pool.get('ud_monitoria.documentos_orientador')._table,
            'disc': self._table,
            'ids': str(ids).lstrip('[(').rstrip(']),').replace('L', '')
        })
        if cr.fetchall()[0][0]:
            raise osv.except_osv(
                u'Erro ao excluir a disciplina',
                u'Não é possível excluir disciplinas quando há orientadores com documentos anexados.'
            )
        return super(DisciplinaMonitoria, self).unlink(cr, uid, ids, context)

    # Validadores
    def valida_datas(self, cr, uid, ids, context=None):
        """
        Valida se a data inicial ocorre antes ou é igual a final.
        """
        for disc in self.browse(cr, uid, ids, context=context):
            if datetime.strptime(disc.data_inicial, DEFAULT_SERVER_DATE_FORMAT) >= datetime.strptime(disc.data_final, DEFAULT_SERVER_DATE_FORMAT):
                return False
        return True

    def valida_valor_negativo(self, cr, uid, ids, context=None):
        for disc in self.browse(cr, uid, ids, context):
            if disc.bolsas < 0 or disc.monitor_s_bolsa < 0 or disc.tutor_s_bolsa < 0:
                return False
        return True

    def valida_bolsas(self, cr, uid, ids, context=None):
        """
        Verifica se o total de bolsas das disciplinas ultrapassa o máximo de bolsas de seu curso.

        :return: True, se não utrapassa, False, caso contrário.
        """
        for disc in self.browse(cr, uid, ids, context):
            bolsas = 0
            for outra_disc in disc.bolsas_curso_id.disciplina_ids:
                if outra_disc.id != disc.id:
                    bolsas += outra_disc.bolsas
            if disc.bolsas_curso_id.bolsas < (bolsas + disc.bolsas):
                return False
        return True

    def valida_bolsas_utilizadas(self, cr, uid, ids, context=None):
        """
        Verifica se o número de bolsas é maior ou igual ao número de bolsas utilizadas.

        :return: True, se satisfazer o critério, False, caso contrário.
        """
        for disc in self.browse(cr, uid, ids, context):
            if disc.bolsas < disc.bolsas_utilizadas:
                return False
        return True

    def valida_disciplina(self, cr, uid, ids, context=None):
        """
        Verifica se a disciplina pertence ao curso selecionado.
        """
        for disc in self.browse(cr, uid, ids, context):
            if disc.bolsas_curso_id.curso_id.id != disc.disciplina_id.ud_disc_id.id:
                return False
        return True

    def valida_orientadores(self, cr, uid, ids, context=None):
        """
        Verifica se a disciplina contém ao menos um orientador.
        """
        for disc in self.browse(cr, uid, ids, context):
            if not disc.orientador_ids:
                return False
        return True

    # Ações após alteração de valor na view
    def onchange_curso(self, cr, uid, ids, curso_id, context=None):
        res = {'value': {'disciplina_id': False, 'bolsas': 0}}
        if curso_id:
            res['domain'] = {
                'disciplina_id': [
                    ('ud_disc_id', '=', self.pool.get('ud_monitoria.bolsas_curso').browse(cr, SUPERUSER_ID, curso_id).curso_id.id)
                ]
            }
        return res
