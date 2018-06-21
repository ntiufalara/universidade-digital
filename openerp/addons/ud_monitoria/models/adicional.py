# coding: utf-8
from datetime import datetime
from re import finditer

from openerp import SUPERUSER_ID
from openerp.osv import fields, osv, orm
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
    _order = 'bolsas_curso_id'

    # Métodos para campos funcionais
    def get_dados_bolsas(self, cr, uid, ids, campo, args, context=None):
        """
        Calcula o número de bolsas utilizadas e disponiveis para uso.

        :return: {ID_MODELO: {'disponiveis': QTD_BOLSAS_DISPONIVEIS, 'utilizadas': QTD_BOLSAS_UTILIZADAS}}
        """
        res = {}
        doc_discente = self.pool.get('ud_monitoria.documentos_discente')
        for disc in self.browse(cr, uid, ids, context):
            utilizadas = doc_discente.search_count(cr, SUPERUSER_ID, [('state', '=', 'bolsista'), ('disciplina_id', '=', disc.id)])
            res[disc.id] = {
                'bolsas_disponiveis': disc.bolsistas - utilizadas,
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
        Busca os ids das disciplinas de monitoria quando o campo "state" dos documentos do discente é atualizado para
        um valor diferente de 'reserva' e o semestre correspondente está ativo.

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
            %(disc)s disc INNER JOIN %(doc)s doc ON (disc.id = doc.disciplina_id)
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
        'disciplina_ids': fields.many2many('ud.disciplina', 'ud_monitoria_disciplinas_rel', 'disc_monitoria', 'disciplina_ud', string=u'Disciplina(s)', required=True, ondelete='restrict'),
        'tutoria': fields.boolean(u'Tutoria?', help=u'Informa se registro será para tutoria'),
        'bolsistas': fields.integer(u'Bolsistas', required=True, help=u'Número de discentes bolsistas'),
        'colaboradores': fields.integer(u'Colaboradores', required=True, help=u'Número de discentes sem bolsa'),
        'bolsas_disponiveis': fields.function(
            get_dados_bolsas, type='integer', string=u'Bolsas sem uso', multi='bolsas_disciplina_monitoria',
            store={
                'ud_monitoria.documentos_discente': (update_bolsas_utilizadas, ['state'], 9),
                'ud_monitoria.disciplina': (lambda cls, cr, uid, ids, ctx=None: ids, ['bolsistas'], 9),
            }
        ),
        'bolsas_utilizadas': fields.function(
            get_dados_bolsas, type='integer', string=u'Bolsas utilizadas', multi='bolsas_disciplina_monitoria',
            store={
                'ud_monitoria.documentos_discente': (update_bolsas_utilizadas, ['state'], 9),
                'ud_monitoria.disciplina': (lambda cls, cr, uid, ids, ctx=None: ids, ['bolsistas'], 9),
            }
        ),
        'perfil_id': fields.many2one('ud.perfil', u'SIAPE', required=True, ondelete='restrict', domain="[('tipo', '=', 'p')]"),
        'orientador_id': fields.related('perfil_id', 'ud_papel_id', type='many2one', relation='ud.employee', readonly=True, string=u'Orientador'),
        'data_inicial': fields.date(u'Data Inicial', required=True),
        'data_final': fields.date(u'Data Final', required=True),
        'is_active': fields.function(get_is_active, type='boolean', string=u'Ativo'),
        'bolsista_ids': fields.function(get_discentes, type='many2many', relation='ud_monitoria.documentos_discente',
                                        string=u'Bolsistas', multi='disciplina_monitoria_discentes'),
        'n_bolsista_ids': fields.function(get_discentes, type='many2many', relation='ud_monitoria.documentos_discente',
                                          string=u'Não Bolsistas', multi='disciplina_monitoria_discentes'),
        'reserva_ids': fields.function(get_discentes, type='many2many', relation='ud_monitoria.documentos_discente',
                                       string=u'Cadastro de Reserva', multi='disciplina_monitoria_discentes'),
        'desligado_ids': fields.function(get_discentes, type='many2many', relation='ud_monitoria.documentos_discente',
                                         string=u'Cadastro de Reserva', multi='disciplina_monitoria_discentes'),
    }
    _constraints = [
        (lambda cls, *args, **kwargs: cls.valida_datas(*args, **kwargs),
         u'A data inicial deve ocorrer antes da data final.', [u'Data inicial e Data final']),
        (lambda cls, *args, **kwargs: cls.valida_bolsas(*args, **kwargs),
         u'O total de bolsas das disciplinas não pode ultrapassar a quatidade máxima definida em seu curso.', [u'Bolsistas']),
        (lambda cls, *args, **kwargs: cls.valida_bolsas_utilizadas(*args, **kwargs),
         u'O número de bolsas não pode ser menor que o número de bolsas utilizadas.', [u'Bolsas utilizadas']),
        (lambda cls, *args, **kwargs: cls.valida_disciplinas_curso(*args, **kwargs),
         u'A disciplina deve pertencer ao curso selecionado.', [u'Disciplina(s)']),
        (lambda cls, *args, **kwargs: cls.valida_disciplina_monitoria(*args, **kwargs),
         u'Para monitoria, apenas uma disciplina deve ser selecionada.', [u'Disciplina(s)']),
        (lambda cls, *args, **kwargs: cls.valida_disciplina_tutoria(*args, **kwargs),
         u'Para tutoria, é possível selecionar até três disciplinas.', [u'Disciplina(s)']),
        (lambda cls, *args, **kwargs: cls.valida_vagas(*args, **kwargs),
         u'Não são permitidos valores negativos para o número de vagas.', [u'Bolsistas / Colaboradores']),
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
                disc_m.id
            FROM
                %(disc_m)s disc_m INNER JOIN ud_monitoria_disciplinas_rel disc_rel ON (disc_m.id = disc_rel.disc_monitoria)
                    INNER JOIN %(disc)s disc ON (disc_rel.disciplina_ud = disc.id)
            WHERE
                %(condicoes)s;
            ''' % {
                'disc_m': self._table,
                'disc': self.pool.get('ud.disciplina')._table,
                'condicoes': condicoes
            })
            args += [('id', 'in', map(lambda l: l[0], cr.fetchall()))]
        return self.name_get(cr, uid, self.search(cr, uid, args, limit=limit, context=context), context)

    def create(self, cr, uid, vals, context=None):
        res = super(DisciplinaMonitoria, self).create(cr, uid, vals, context)
        self.add_grupo_orientador(cr, uid, [res], context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        orientadores = None
        if 'perfil_id' in vals:
            if isinstance(ids, (int, long)):
                ids = [ids]
            orientadores = [disc['perfil_id'] for disc in self.read(cr, uid, ids, ['perfil_id'], load='_classic_write')]
        super(DisciplinaMonitoria, self).write(cr, uid, vals, context)
        if orientadores:
            self.remove_grupo_orientador(cr, uid, perfis=orientadores, context=context)
            self.add_grupo_orientador(cr, uid, ids, context)
        return True

    def unlink(self, cr, uid, ids, context=None):
        """
        Impede que a disciplina seja deleta caso o orientador possua algum documento. Verifica e remove do grupo de
        segurança se não houver mais vínculo com disciplinas.
        """
        if isinstance(ids, (int, long)):
            ids = [ids]
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
        if cr.fetchone()[0]:
            raise orm.except_orm(
                u'Exclusão não permitida!',
                u'Não é possível excluir disciplinas quando seu orientador possui algum documento anexado.'
            )
        perfis = list(set([disc['perfil_id'] for disc in self.read(cr, uid, ids, ['perfil_id'], load='_classic_write')]))
        super(DisciplinaMonitoria, self).unlink(cr, uid, ids, context)
        self.remove_grupo_orientador(cr, uid, perfis=perfis, context=context)
        return True

    def default_get(self, cr, uid, fields_list, context=None):
        """
        === Extensão do método osv.Model.default_get
        Adiciona um curso padrão no campo correspondente quando disciplina for criada por usando o filtro de coordenador
        de monitoria de algum curso.
        """
        context = context or {}
        res = super(DisciplinaMonitoria, self).default_get(cr, uid, fields_list, context)
        if context.get('bolsas_curso_id', False):
            res['bolsas_curso_id'] = context['bolsas_curso_id']
            res['semestre_id'] = context.get("semestre_id", False) or self.pool.get('ud_monitoria.bolsas_curso').read(
                cr, SUPERUSER_ID, context['bolsas_curso_id'], ['semestre_id'], load='_classic_write'
            )['semestre_id']
        elif context.get("semestre_id", None):
            res['semestre_id'] = context['semestre_id']
        elif context.get('active_model', False) == 'ud_monitoria.semestre' and context.get('active_id', False):
            res['semestre_id'] = context['active_id']
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
        Define o filtro de cursos de acordo com os que estão listados nas configurações do semestre. Caso seja definido
        para filtrar pelo coordenador do curso de monitoria usando o marcador em "context", a lista já filtrada  será
        limitada aos cursos que o usuário logado está como coordenador de monitoria.
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
        if 'disciplina_ids' in res['fields']:
            if context.get('curso_id', False):
                curso_id = context['curso_id']
            elif context.get('bolsas_curso_id', False):
                curso_id = self.pool.get('ud_monitoria.bolsas_curso').read(
                    cr, SUPERUSER_ID, context['bolsas_curso_id'], ['curso_id'], load='_classic_write'
                )['curso_id']
            else:
                return res
            domain_temp = res["fields"]["disciplina_ids"].get("domain", [])
            if isinstance(domain_temp, str):
                domain_temp = list(eval(domain_temp))
            domain = []
            for d in domain_temp:
                if d[0] != "id":
                    domain.append(d)
            del domain_temp
            res["fields"]["disciplina_ids"]['domain'] = domain + [
                ('id', 'in', self.pool.get('ud.disciplina').search(cr, SUPERUSER_ID, [('ud_disc_id', '=', curso_id)]))
            ]
        return res

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        """
        === Extensão do método osv.Model.search
        Foi adicionado a opção de filtrar as disciplinas em que o usuário logado esteja vinculado como coordenador de
        monitoria do curso correspondente.
        """
        context = context or {}
        if context.get("coordenador_monitoria_curso", False):
            pessoa_id = get_ud_pessoa_id(self, cr, uid)
            if not pessoa_id:
                return []
            curso_ids = self.pool.get("ud.curso").search(cr, SUPERUSER_ID, [("coord_monitoria_id", "=", pessoa_id)])
            curso_ids = self.pool.get('ud_monitoria.bolsas_curso').search(cr, SUPERUSER_ID,
                                                                          [('curso_id', 'in', curso_ids)])
            args = (args or []) + [("bolsas_curso_id", "in", curso_ids)]
        if context.get("disciplina_ativa", False):
            hoje = data_hoje(self, cr).strftime(DEFAULT_SERVER_DATE_FORMAT)
            args = (args or []) + [('data_inicial', '<=', hoje), ('data_final', '>=', hoje)]
        if context.get('disciplinas_semestre', False):
            semestre = context.get('semestre_id', context['active_id'] if context.get('active_model', False) == 'ud_monitoria.semestre' else False)
            if not semestre:
                return []
            res = super(DisciplinaMonitoria, self).search(cr, uid, args, offset, limit, order, context, count)
            if not res:
                return []
            cr.execute('''
            SELECT
                disc.id
            FROM
                %(disc)s disc INNER JOIN %(bc)s bc ON (disc.bolsas_curso_id = bc.id)
            WHERE
                disc.id in (%(ids)s) and bc.semestre_id = %(id)s;
            ''' % {
                'disc': self._table,
                'bc': self.pool.get('ud_monitoria.bolsas_curso')._table,
                'ids': str(res).lstrip('[(').rstrip(']),').replace('L', ''),
                'id': semestre,
            })
            return map(lambda l: l[0], cr.fetchall())
        return super(DisciplinaMonitoria, self).search(cr, uid, args, offset, limit, order, context, count)

    # Adição e remoção do grupo de segurança
    def add_grupo_orientador(self, cr, uid, ids, context=None):
        """
        Adiciona um orientandor no grupo de permissões.

        :raise orm.except_orm: Se perfil do orientador não possuir vínculo com algum usuário.
        """
        if isinstance(ids, (int, long)):
            ids = [ids]
        group = self.pool.get('ir.model.data').get_object(
            cr, SUPERUSER_ID, 'ud_monitoria', 'group_ud_monitoria_orientador', context
        )
        for disc in self.browse(cr, uid, ids, context):
            if not disc.orientador_id.user_id:
                if disc.orientador_id.cpf:
                    comp = '(CPF: %s)' % disc.orientador_id.cpf
                else:
                    comp = '(SIAPE: %s)' % disc.perfil_id.matricula
                raise orm.except_orm(
                    u'Usuário não encontrado',
                    u'O(a) orientador(a) "%s" %s não possui login de usuário.' % (disc.orientador_id.name, comp)
                )
            group.write({'users': [(4, disc.orientador_id.user_id.id)]})

    def remove_grupo_orientador(self, cr, uid, ids=None, perfis=None, context=None):
        """
        Remove um orientador do grupo de permissões se não tiver mais nenhum vínculo com disciplinas.
        """
        group = self.pool.get('ir.model.data').get_object(
            cr, SUPERUSER_ID, 'ud_monitoria', 'group_ud_monitoria_orientador', context
        )
        perfil_model = self.pool.get('ud.perfil')
        if perfis:
            sql = '''
            SELECT
                usu.id
            FROM
                %(per)s per LEFT JOIN %(disc)s disc ON (per.id = disc.perfil_id)
                    INNER JOIN %(pes)s pes ON (per.ud_papel_id = pes.id)
                        INNER JOIN %(res)s res ON (pes.resource_id = res.id)
                            INNER JOIN %(usu)s usu ON (res.user_id = usu.id)
            WHERE
                per.id in (%(perfis)s) AND disc.id is null;
            ''' % {
                'disc': self._table,
                'per': perfil_model._table,
                'pes': self.pool.get('ud.employee')._table,
                'res': self.pool.get('resource.resource')._table,
                'usu': self.pool.get('res.users')._table,
                'perfis': str(perfis).lstrip('([').rstrip(']),').replace('L', '')
            }
            cr.execute(sql)
            res = cr.fetchall()
            if res:
                remove = []
                for usuario in res:
                    remove.append((3, usuario[0]))
                if remove:
                    group.write({'users': remove})
        if ids:
            remove = []
            for doc in self.browse(cr, uid, ids, context):
                perfis = perfil_model.search(cr, SUPERUSER_ID, [('ud_papel_id', '=', doc.orientador_id.id)])
                if not self.search_count(cr, SUPERUSER_ID, [('perfil_id', 'in', perfis)]) and doc.orientador_id.user_id:
                    remove.append((3, doc.orientador_id.user_id.id))
            if remove:
                group.write({'users': remove})

    # Validadores
    def valida_datas(self, cr, uid, ids, context=None):
        """
        Valida se a data inicial ocorre antes ou é igual a final.
        """
        for disc in self.browse(cr, uid, ids, context=context):
            if datetime.strptime(disc.data_inicial, DEFAULT_SERVER_DATE_FORMAT) >= datetime.strptime(disc.data_final, DEFAULT_SERVER_DATE_FORMAT):
                return False
        return True

    def valida_vagas(self, cr, uid, ids, context=None):
        for disc in self.browse(cr, uid, ids, context):
            if disc.bolsistas < 0 or disc.colaboradores < 0:
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
                    bolsas += outra_disc.bolsistas
            if disc.bolsas_curso_id.bolsas < (bolsas + disc.bolsistas):
                return False
        return True

    def valida_bolsas_utilizadas(self, cr, uid, ids, context=None):
        """
        Verifica se o número de bolsas é maior ou igual ao número de bolsas utilizadas.

        :return: True, se satisfazer o critério, False, caso contrário.
        """
        for disc in self.browse(cr, uid, ids, context):
            if disc.bolsistas < disc.bolsas_utilizadas:
                return False
        return True

    def valida_disciplina_monitoria(self, cr, uid, ids, context=None):
        """
        Verifica se a quantidade de disciplinas para monitoria é apenas uma e se ocorre apenas uma vez no semestre para
        o mesmo orientador.
        """
        for disc in self.browse(cr, uid, ids, context):
            if not disc.tutoria and len(disc.disciplina_ids) != 1:
                raise orm.except_orm(
                    u'Erro de validação!',
                    u'Na modalidade "Monitoria", um registro de disciplina deve ter vínculo de apenas uma disciplina.'
                )
        # TODO: Implementar a verificação de unicidade de conjunto de disciplinas por seu orientador no smemestre.
        return True

    def valida_disciplina_tutoria(self, cr, uid, ids, context=None):
        """
        Verifica se a disciplina de tutoria possui no máximo 3 disciplinas e o conjunto ser único para um orientador.
        """
        for disc in self.browse(cr, uid, ids, context):
            if disc.tutoria and len(disc.disciplina_ids) > 3:
                raise orm.except_orm(
                    u'Erro de validação!',
                    u'Na modalidade "Tutoria", um registro de disciplina deve possuir 3 disciplinas, no máximo.'
                )
        # TODO: Implementar a verificação de unicidade de conjunto de disciplinas por seu orientador no smemestre.
        return True

    def valida_disciplinas_curso(self, cr, uid, ids, context=None):
        """
        Verifica se a disciplina pertence ao curso selecionado.
        """
        for disc in self.browse(cr, uid, ids, context):
            for disc_ud in disc.disciplina_ids:
                if disc.bolsas_curso_id.curso_id.id != disc_ud.ud_disc_id.id:
                    return False
        return True

    # Ações após alteração de valor na view
    def onchange_curso(self, cr, uid, ids, curso_id, context=None):
        res = {'value': {'disciplina_ids': False, 'semestre_id': False, 'bolsistas': 0}, 'domain': {'disciplina_ids': [('id', '=', False)]}}
        if curso_id:
            bc = self.pool.get('ud_monitoria.bolsas_curso').browse(cr, SUPERUSER_ID, curso_id)
            res['domain']['disciplina_ids'] = [
                ('ud_disc_id', '=', bc.curso_id.id)
            ]
            res['value']['semestre_id'] = bc.semestre_id.id
        return res

    def onchange_perfil(self, cr, uid, ids, perfil_id, context=None):
        """
        Método usado para atualizar os dados do campo "orientador_id" caso "perfil_id" seja modificado.
        """
        if perfil_id:
            return {"value": {"orientador_id": self.pool.get("ud.perfil").read(
                cr, SUPERUSER_ID, perfil_id, ["ud_papel_id"], context=context
            ).get("ud_papel_id")}}
        return {"value": {"orientador_id": False}}

    def onchange_modalidade_disciplina(self, cr, uid, ids, tutoria, disciplinas):
        if tutoria and len(disciplinas[0][2]) > 3:
            return {
                'warning': {'title': u'Alerta', 'message': u'É permitido selecionar no máximo 3 disciplinas para Tutoria.'},
                'value': {
                    'disciplina_ids': disciplinas[0][2][:3]
                }
            }
        if not tutoria and len(disciplinas[0][2]) > 1:
            return {
                'warning': {'title': u'Alerta', 'message': u'É permitido selecionar apenas uma disciplina para monitoria.'},
                'value': {
                    'disciplina_ids': [disciplinas[0][2][0]]
                }
            }
        return {}
