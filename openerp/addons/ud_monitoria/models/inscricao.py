# coding: utf-8
from datetime import datetime
from openerp import SUPERUSER_ID
from openerp.osv import fields, osv, orm
from openerp.addons.ud.ud import _TIPOS_BOLSA
from util import get_ud_pessoa, get_ud_pessoa_id, data_hoje


TIPOS_BOLSA = dict(_TIPOS_BOLSA)


class Pontuacao(osv.Model):
    _name = 'ud_monitoria.pontuacao'
    _description = u'Pontuação de cada critério (UD)'
    _rec_name = 'criterio_avaliativo_id'
    _columns = {
        'criterio_avaliativo_id': fields.many2one('ud_monitoria.criterio_avaliativo', u'Critério Avaliativo',
                                                  readonly=True, ondelete='restrict'),
        'pontuacao': fields.float(u'Pontuação', required=True),
        'info': fields.text(u'Informações adicionais'),
        'inscricao_id': fields.many2one('ud_monitoria.inscricao', u'Inscrição', invisible=True, ondelete='cascade'),
    }
    _defaults = {
        'pontuacao': 0.,
    }
    _constraints = [
        (lambda cls, *args, **kwargs: cls.valida_pontuacao(*args, **kwargs),
         u'Toda pontuação deve está entre 0 e 10.', [u'Pontuação'])
    ]

    # Métodos sobrescritos
    def name_get(self, cr, uid, ids, context=None):
        """
        === Sobrescrita do método osv.Model.name_get
        Define a forma de visualização desse modelo em campos many2one.
        """
        return [(pont.id, u'%s (%d)' % pont.criterio_avaliativo_id.name, pont.pontuacao) for pont in
                self.browse(cr, uid, ids, context=context)]

    def name_search(self, cr, uid, name='', args=None, operator='ilike', context=None, limit=100):
        """
        === Sobrescrita do método osv.Model.name_search
        Define a forma de pesquisa desse modelo em campos many2one.
        """
        if not isinstance(args, (list, tuple)):
            args = []
        if not (name == '' and operator == 'ilike'):
            criterios_ids = self.pool.get('ud_monitoria.criterio_avaliativo').search(cr, uid,
                                                                                     [('name', operator, name)],
                                                                                     context=context)
            args += [('criterio_avaliativo_id', 'in', criterios_ids)]
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


class Inscricao(osv.Model):
    _name = 'ud_monitoria.inscricao'
    _description = u'Inscrição de Monitoria (UD)'
    _order = 'state asc, processo_seletivo_id asc, perfil_id asc'
    _STATES = [('analise', u'Em Análise'), ('classificado', u'Classificado(a)'),
               ('desclassificado', u'Desclassificado(a)'), ('reserva', u'Cadastro de Reserva')]

    # Métodos para campos calculados
    def calcula_media(self, cr, uid, ids, campos, args, context=None):
        """
        Calcula a média das pontuações da disciplina.
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
        for inscricao in self.browse(cr, uid, ids, context=context):
            if inscricao.processo_seletivo_id.tipo_media == 'a':
                res[inscricao.id] = media_aritmetica(inscricao.pontuacoes_ids)
            if inscricao.processo_seletivo_id.tipo_media == 'p':
                res[inscricao.id] = media_ponderada(inscricao.pontuacoes_ids)
        return res

    def get_concorrencia(self, cr, uid, ids, campos, args, context=None):
        res = {}
        for insc in self.browse(cr, uid, ids, context):
            qtd = self.search_count(
                cr, uid, [('disciplina_id', '=', insc.disciplina_id.id), ('bolsista', '=', insc.bolsista)]
            )
            if insc.bolsista:
                res[insc.id] = insc.disciplina_id.bolsistas < qtd
            else:
                res[insc.id] = insc.disciplina_id.colaboradores < qtd
        return res

    def atualiza_media_pont(self, cr, uid, ids, context=None):
        """
        Gatilho para atualizar a pontuação dada a algum critério avaliativo dessa disciplina.

        :attetion: O modelo de "self" passa a ser o que está no gatilho do campo function em vez do objeto atual.
        """
        return [
            pont.inscricao_id.id for pont in self.browse(cr, uid, ids, context) if pont.inscricao_id
        ]

    def atualiza_media_peso(self, cr, uid, ids, context=None):
        """
        Gatilho para atualizar a média o peso de caso algum critério avaliativo do processo seletivo seja alterado.

        :attetion: O modelo de "self" passa a ser o que está no gatilho do campo function em vez do objeto atual.
        """
        cr.execute('''
        SELECT
            insc.id
        FROM
            %(insc)s insc INNER JOIN %(pont)s pont ON (insc.id = pont.inscricao_id)
                INNER JOIN %(crit)s crit ON (pont.criterio_avaliativo_id = crit.id)
                    INNER JOIN %(ps)s ps ON (crit.processo_seletivo_id = ps.id)
        WHERE
            crit.id in (%(ids)s) AND ps.tipo_media = 'p'
        ''' % {
            'insc': self.pool.get('ud_monitoria.inscricao')._table,
            'pont': self.pool.get('ud_monitoria.pontuacao')._table,
            'ps': self.pool.get('ud_monitoria.processo_seletivo')._table,
            'crit': self.pool.get('ud_monitoria.criterio_avaliativo')._table,
            'ids': str(ids).lstrip('([').rstrip(')],').replace('L', ''),
        })
        return map(lambda l: l[0], cr.fetchall())

    _columns = {
        'id': fields.integer('ID', invisible=True, readonly=True),
        # Dados Pessoais
        'perfil_id': fields.many2one('ud.perfil', u'Matrícula', required=True, ondelete='restrict', domain=[('tipo', '=', 'a')]),
        'curso_id': fields.related('perfil_id', 'ud_cursos', type='many2one', relation='ud.curso', string=u'Curso',
                                   readonly=True, help='Curso que o discente possui vínculo'),
        'discente_id': fields.related('perfil_id', 'ud_papel_id', type='many2one', relation='ud.employee',
                                      string=u'Discente', readonly=True),
        'telefone_fixo': fields.related('perfil_id', 'ud_papel_id', 'work_phone', string='Telefone fixo', type='char'),
        'celular': fields.related('perfil_id', 'ud_papel_id', 'mobile_phone', string='Celular', type='char', required=True),
        'email': fields.related('perfil_id', 'ud_papel_id', 'work_email', string='E-mail', type='char', required=True),
        'whatsapp': fields.char(u'WhatsApp', size=15, required=True),
        # Arquivos
        'cpf': fields.binary(u'CPF', required=True),
        'identidade': fields.binary(u'RG', required=True),
        'hist_analitico': fields.binary(u'Hist. Analítico', required=True),
        'certidao_vinculo': fields.binary(u'Certidão de Vínculo', required=True),
        'processo_seletivo_id': fields.many2one('ud_monitoria.processo_seletivo', u'Processo Seletivo', required=True,
                                                ondelete='restrict'),
        'tutoria': fields.boolean(u'Tutoria?'),
        'bolsas_curso_id': fields.many2one('ud_monitoria.bolsas_curso', u'Curso', required=True, ondelete='restrict'),
        'disciplina_id': fields.many2one('ud_monitoria.disciplina_ps', u'Disciplina(s)', required=True, ondelete='restrict',
                                         domain='[("processo_seletivo_id", "=", processo_seletivo_id), ("bolsas_curso_id", "=", bolsas_curso_id), ("tutoria", "=", tutoria)]'),
        'pontuacoes_ids': fields.one2many('ud_monitoria.pontuacao', 'inscricao_id', u'Pontuações', readonly=True),
        'media': fields.function(
            calcula_media, type='float', string=u'Média',
            store={'ud_monitoria.pontuacao': (atualiza_media_pont, ['pontuacao'], 10),
                   'ud_monitoria.criterio_avaliativo': (atualiza_media_peso, ['peso'], 10)},
            help=u'Cálculo da média de acordo com os critérios avaliativos do processo seletivo'
        ),
        'bolsista': fields.boolean(u'Bolsista?'),
        'dados_bancarios_id': fields.many2one('ud.dados.bancarios', u'Dados Bancários', ondelete='restrict',
                                              domain='[("ud_conta_id", "=", discente_id)]', context='{"ud_conta_id": discente_id}'),
        'info': fields.text(u'Informações Adicionais', readonly=True),
        'state': fields.selection(_STATES, u'Status', readonly=True, required=True),
        # Campos de controle
        'cpf_nome': fields.char(u'Arquivo CPF'),
        'identidade_nome': fields.char(u'Arquivo RG'),
        'hist_analitico_nome': fields.char(u'Arquivo Hist. Analítico'),
        'certidao_vinculo_nome': fields.char(u'Arquivo Certidão de Vínculo'),
        'com_concorrencia': fields.function(get_concorrencia, type='boolean', string=u'Possui concorrência?'),
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
    _defaults = {
        'state': 'analise',
    }

    # Métodos sobrescritos
    def name_get(self, cr, uid, ids, context=None):
        """
        === Sobrescrita do método osv.Model.search
        Define como inscrição será visualizada em campos many2one.
        """
        res = []
        for insc in self.browse(cr, SUPERUSER_ID, ids, context=context):
            res.append((insc.id, u'%s (Matrícula: %s)' % (insc.discente_id.name, insc.perfil_id.matricula)))
        return res

    def name_search(self, cr, uid, name='', args=None, operator='ilike', context=None, limit=100):
        """
        === Sobrescrita do método osv.Model.search
        Ao pesquisar inscrições em campos many2one, será pesquisado pelo nome do discente ou matrícula.
        """
        discentes_ids = self.pool.get('ud.employee').search(cr, uid, [('name', operator, name)], context=context)
        args += [('discente_id', 'in', discentes_ids)]
        perfil_model = self.pool.get('ud.perfil')
        for perfil in perfil_model.search(cr, uid, [('matricula', '=', name)]):
            discentes_ids.append(perfil_model.browse(cr, uid, perfil, context).ud_papel_id.id)
        ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)

    def default_get(self, cr, uid, fields_list, context=None):
        res = super(Inscricao, self).default_get(cr, uid, fields_list, context)
        context = context or {}
        if context.get('active_model', False) != 'ud_monitoria.processo' and context.get('active_id', False):
            res['processo_seletivo_id'] = context['active_id']
            res['pontuacoes_ids'] = [
                (0, 0, {'criterio_avaliativo_id': crit})
                for crit in self.pool.get('ud_monitoria.processo_seletivo').read(
                    cr, uid, context['active_id'], ['criterios_avaliativos_ids'], load='_classic_write'
                )['criterios_avaliativos_ids']
            ]
        return res

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = super(Inscricao, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
        context = context or {}
        if context.get('active_model', False) == 'ud_monitoria.processo_seletivo' and context.get('active_id', False):
            grupos = 'ud_monitoria.group_ud_monitoria_coordenador,ud_monitoria.group_ud_monitoria_administrador'
            if self.user_has_groups(cr, uid, grupos, context):
                return res
            pessoa = get_ud_pessoa(self, cr, uid)
            if not pessoa:
                raise orm.except_orm(
                    u'Usuário não cadastrado',
                    u'O usuário atual (%s) não possui registros no núcleo.' % self.pool.get('res.users').read(
                        cr, SUPERUSER_ID, uid, ['login'], load='_classic_write'
                    )['login']
                )
            if 'perfil_id' in res['fields']:
                domain = res["fields"]["perfil_id"].get("domain", [])
                if isinstance(domain, str):
                    domain = list(eval(domain))
                res["fields"]["perfil_id"]["domain"] = domain + [('id', 'in', [p.id for p in pessoa.papel_ids])]
        return res

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        """
        === Extensão do método osv.Model.search
        Filtra as inscrições se context tiver a chave para filtrar discente e/ou orientador. A primeira opção limita as
        inscrições ao proprietário da mesma, a segunda limita as inscrições pelas disciplinas que foram selecionadas
        na inscrição. É necessário saber que a primeira pode influenciar no resultado da segunda.
        """
        context = context or {}
        pessoa_id = None
        if context.pop('filtrar_discente', False):
            pessoa_id = get_ud_pessoa_id(self, cr, uid)
            if not pessoa_id:
                return []
            perfis = self.pool.get('ud.perfil').search(cr, SUPERUSER_ID, [('ud_papel_id', '=', pessoa_id)])
            args += [('perfil_id', 'in', perfis)]
        res = super(Inscricao, self).search(cr, uid, args, offset, limit, order, context, count)
        if res and context.get('filtrar_orientador', False):
            if not pessoa_id:
                pessoa_id = get_ud_pessoa_id(self, cr, uid)
                if not pessoa_id:
                    return []
                perfis = self.pool.get('ud.perfil').search(cr, SUPERUSER_ID, [('ud_papel_id', '=', pessoa_id)],
                                                           context=context)
                if not perfis:
                    return []
            cr.execute('''
            SELECT
                insc.id
            FROM
                %(insc)s insc INNER JOIN %(disc_ps)s disc_ps ON (insc.disciplina_id = disc_ps.id)
                    INNER JOIN %(disc)s disc ON (disc_ps.disc_monit_id = disc.id)
            WHERE
                insc.id in (%(ids)s) AND disc.perfil_id in (%(perfis)s)
            ''' % {
                'insc': self._table,
                'disc_ps': self.pool.get('ud_monitoria.disciplina_ps')._table,
                'disc': self.pool.get('ud_monitoria.disciplina')._table,
                'ids': str(res).lstrip('([').rstrip(')],').replace('L', ''),
                'perfis': str(perfis).lstrip('([').rstrip(')],').replace('L', ''),
            })
            res = map(lambda l: l[0], cr.fetchall())
        return res

    # Validadores
    def valida_processo_seletivo(self, cr, uid, ids, context=None):
        """
        Verifica se o processo seletivo correspondente é inválido.
        """
        for insc in self.browse(cr, uid, ids, context=context):
            if insc.processo_seletivo_id.state in ['invalido', 'demanda', 'novo']:
                return False
        return True

    # Ações de botões
    def classificar_direto(self, cr, uid, ids, context=None, validador=lambda insc: None):
        """
        Aprova o discente ignorando a pontuação obtida.

        :except orm.except_orm: Caso haja alguma inscrição com status diferente de 'analise'.
                                Se a inscrição for aprovar como bolsista e o discente já estiver vinculado a outra bolsa.
                                Se o processo seletivo não estiver encerrado.
                                Se existir inscrições para bolsista não avaliadas enquanto torna um discente colaborador como bolsista.
                                Se não tiver as permissões corretas para realizar a ação.
        """
        context = context or {}
        perfil_model = self.pool.get('ud.perfil')
        doc_discente = self.pool.get('ud_monitoria.documentos_discente')
        doc_orientador = self.pool.get('ud_monitoria.documentos_orientador')
        hoje = data_hoje(self, cr, uid)
        grupos = [
            'ud_monitoria.group_ud_monitoria_orientador',
            'ud_monitoria.group_ud_monitoria_coordenador,ud_monitoria.group_ud_monitoria_administrador',
        ]
        if not self.user_has_groups(cr, uid, ','.join(grupos)):
            raise orm.except_orm(
                u'Acesso Negado!',
                u'Você não possui permissão para realizar essa ação'
            )
        for insc in self.browse(cr, uid, ids, context):
            if not self.user_has_groups(cr, uid, grupos[1]):
                if not self.user_has_groups(cr, uid, grupos[0]):
                    raise orm.except_orm(
                        u'Acesso Negado!',
                        u'Você não faz parte de nenhum grupo de segurança que permite alterar o status de inscrições.'
                    )
                elif insc.disciplina_id.orientador_id.user_id.id != uid:
                    raise orm.except_orm(
                        u'Acesso Negado!',
                        u'Você não é o orientador da disciplina da inscrição atual.'
                    )
            if insc.processo_seletivo_id.state != 'encerrado':
                raise orm.except_orm(
                    u'Ação inválida',
                    u'Não é possível alterar o status da inscrição enquanto o processo seletivo não estiver encerrado.'
                )
            if insc.state != 'analise':
                raise orm.except_orm(
                    u'Ação não permitida',
                    u'Não é possível mudar o status de inscrições já avaliadas.'
                )
            validador(insc)
            state = 'n_bolsista'
            if insc.bolsista:
                if context.pop('n_bolsista', False):
                    info = u'%s - Discente aprovado(a) SEM bolsa.' % datetime.strftime(hoje, '%d-%m-%Y')
                    insc.write({'info': '%s%s' % (insc.info and insc.info + '\n' or '', info)})
                elif insc.perfil_id.is_bolsista:
                    raise orm.except_orm(
                        u'Discente bolsista', u'O discente atual está vinculado a uma bolsa do tipo: "{}"'.format(
                            TIPOS_BOLSA[insc.perfil_id.tipo_bolsa]
                        )
                    )
                else:
                    # FIXME: O campo do valor da bolsa no núcleo é um CHAR, se possível, mudar para um FLOAT
                    perfil_model.write(cr, SUPERUSER_ID, insc.perfil_id.id, {
                        'is_bolsista': True, 'tipo_bolsa': 'm',
                        'valor_bolsa': ('%.2f' % insc.processo_seletivo_id.valor_bolsa).replace('.', ',')
                    })
                    state = 'bolsista'
            elif context.pop('bolsista', False):
                if self.search_count(cr, uid, [
                    ('processo_seletivo_id', '=', insc.processo_seletivo_id.id), ('id', '!=', insc.id),
                    ('bolsista', '=', True), ('state', '=', 'analise'),
                ]):
                    raise orm.except_orm(
                        u'Ação bloqueada',
                        u'A ação será desbloqueada quando não houverem inscrições, para discentes bolsistas, para avaliar e classificar.'
                    )
                elif insc.perfil_id.is_bolsista:
                    raise orm.except_orm(
                        u'Discente bolsista', u'O discente atual está vinculado a uma bolsa do tipo: "{}"'.format(
                            TIPOS_BOLSA[insc.perfil_id.tipo_bolsa]
                        )
                    )
                else:
                    # FIXME: O campo do valor da bolsa no núcleo é um CHAR, se possível, mudar para um FLOAT
                    perfil_model.write(cr, SUPERUSER_ID, insc.perfil_id.id, {
                        'is_bolsista': True, 'tipo_bolsa': 'm',
                        'valor_bolsa': ('%.2f' % insc.processo_seletivo_id.valor_bolsa).replace('.', ',')
                    })
                    state = 'bolsista'
                    info = u'%s - Discente aprovado(a) COM bolsa.' % datetime.strftime(hoje, '%d-%m-%Y')
                    insc.write({'info': '%s%s' % (insc.info and insc.info + '\n' or '', info)})
            doc_discente.create(cr, SUPERUSER_ID, {
                'perfil_id': insc.perfil_id.id,
                'dados_bancarios_id': getattr(insc.dados_bancarios_id, 'id', False),
                'disciplina_id': insc.disciplina_id.disc_monit_id.id,
                'tutor': insc.tutoria,
                'state': state,
            }, context)
            args = [('disciplina_id', '=', insc.disciplina_id.disc_monit_id.id),
                    ('perfil_id', '=', insc.disciplina_id.perfil_id.id)]
            if not doc_orientador.search(cr, SUPERUSER_ID, args, limit=1):
                dados = {
                    'disciplina_id': insc.disciplina_id.disc_monit_id.id,
                    'perfil_id': insc.disciplina_id.perfil_id.id,
                }
                doc_orientador.create(cr, SUPERUSER_ID, dados, context)
        self.write(cr, SUPERUSER_ID, ids, {'state': 'classificado'}, context)
        return True

    def classificar_direto_bolsa(self, cr, uid, ids, context=None):
        """
        Classifica o discente como bolsista, mesmo se for colaborador, ignorando sua média.

        :except orm.except_orm: Caso haja alguma inscrição com status diferente de 'analise'.
                                Se a inscrição for aprovar como bolsista e o discente já estiver vinculado a outra bolsa.
                                Se o processo seletivo não estiver encerrado.
                                Caso existam inscrições para bolsista não avaliadas.
                                Se não tiver as permissões corretas para realizar a ação.
        """
        context = context or {}
        context['bolsista'] = True
        return self.classificar_direto(cr, uid, ids, context)

    def classificar_direto_s_bolsa(self, cr, uid, ids, context=None):
        """
        Aprova o discente como colaborador ignorando a pontuação obtida. Caso seja para bolsista, após aprovado, o(a)
        discente passa a ser colaborador(a).

        :except orm.except_orm: Caso haja alguma inscrição com status diferente de 'analise'.
                                Se a inscrição for aprovar como bolsista e o discente já estiver vinculado a outra bolsa.
                                Se o processo seletivo não estiver encerrado.
                                Se não tiver as permissões corretas para realizar a ação.
        """
        context = context or {}
        context['n_bolsista'] = True
        return self.classificar_direto(cr, uid, ids, context)

    def classificar_media(self, cr, uid, ids, context=None):
        """
        Aprova o discente baseado na pontuação obtida.

        :except orm.except_orm: Caso haja alguma inscrição com status diferente de 'analise'.
                                Se a inscrição for aprovar como bolsista e o discente já estiver vinculado a outra bolsa.
                                Se o processo seletivo não estiver encerrado.
                                Se a inscrição não estive com média mínima ao do processo seletivo correspondente.
                                Se não tiver as permissões corretas para realizar a ação.
        """
        def valida_media(insc):
            media_minima = insc.processo_seletivo_id.media_minima
            if insc.media < media_minima:
                raise orm.except_orm(u'Média Insuficiente',
                                     u'A média não atingiu o valor mínimo especificado de %.2f' % media_minima)
        return self.classificar_direto(cr, uid, ids, context, valida_media)

    def classificar_media_bolsa(self, cr, uid, ids, context=None):
        """
        Classifica o discente como bolsista, mesmo se for colaborador, baseado em sua média.

        :except orm.except_orm: Caso haja alguma inscrição com status diferente de 'analise'.
                                Se a inscrição for aprovar como bolsista e o discente já estiver vinculado a outra bolsa.
                                Se o processo seletivo não estiver encerrado.
                                Se a inscrição não estive com média mínima ao do processo seletivo correspondente.
                                Caso existam inscrições para bolsista não avaliadas.
                                Se não tiver as permissões corretas para realizar a ação.
        """
        context = context or {}
        context['bolsista'] = True
        return self.classificar_media(cr, uid, ids, context)

    def classificar_media_s_bolsa(self, cr, uid, ids, context=None):
        """
        Aprova o discente como colaborador baseando na pontuação obtida. Caso seja para bolsista, após aprovado, o(a)
        discente passa a ser colaborador(a).

        :except orm.except_orm: Caso haja alguma inscrição com status diferente de 'analise'.
                                Se a inscrição for aprovar como bolsista e o discente já estiver vinculado a outra bolsa.
                                Se o processo seletivo não estiver encerrado.
                                Se a inscrição não estive com média mínima ao do processo seletivo correspondente.
                                Se não tiver as permissões corretas para realizar a ação.
        """
        context = context or {}
        context['n_bolsista'] = True
        return self.classificar_media(cr, uid, ids, context)

    def cadastro_reserva(self, cr, uid, ids, context=None):
        """
        Cadastra o documento do discente para o cadastro de reserva.

        :except orm.except_orm: Caso haja alguma inscrição com status diferente de 'analise'.
                                Se o processo seletivo não estiver encerrado.
                                Se não tiver as permissões corretas para realizar a ação.
        """
        context = context or {}
        doc_discente = self.pool.get('ud_monitoria.documentos_discente')
        grupos = [
            'ud_monitoria.group_ud_monitoria_orientador',
            'ud_monitoria.group_ud_monitoria_coordenador,ud_monitoria.group_ud_monitoria_administrador',
        ]
        if not self.user_has_groups(cr, uid, ','.join(grupos)):
            raise orm.except_orm(
                u'Acesso Negado!',
                u'Você não possui permissão para realizar essa ação'
            )
        for insc in self.browse(cr, uid, ids, context):
            if not self.user_has_groups(cr, uid, grupos[1]):
                if not self.user_has_groups(cr, uid, grupos[0]):
                    raise orm.except_orm(
                        u'Acesso Negado!',
                        u'Você não faz parte de nenhum grupo de segurança que permite alterar o status de inscrições.'
                    )
                elif insc.disciplina_id.orientador_id.user_id.id != uid:
                    raise orm.except_orm(
                        u'Acesso Negado!',
                        u'Você não é o orientador da disciplina da inscrição atual.'
                    )
            if insc.processo_seletivo_id.state != 'encerrado':
                raise orm.except_orm(
                    u'Ação inválida',
                    u'Não é possível alterar o status da inscrição enquanto o processo seletivo não estiver encerrado.'
                )
            if insc.state != 'analise':
                raise orm.except_orm(
                    u'Ação não permitida',
                    u'Não é possível mudar o status de inscrições já avaliadas.'
                )
            doc_discente.create(cr, SUPERUSER_ID, {
                'perfil_id': insc.perfil_id.id,
                'dados_bancarios_id': getattr(insc.dados_bancarios_id, 'id', False),
                'disciplina_id': insc.disciplina_id.disc_monit_id.id,
                'tutor': insc.tutoria,
                'state': 'reserva',
            }, context)
        self.write(cr, SUPERUSER_ID, ids, {'state': 'reserva'}, context)
        return True

    def desclassificar(self, cr, uid, ids, context=None):
        """
        Desclassifica a inscrição.

        :except orm.except_orm: Caso haja alguma inscrição com status diferente de 'analise'.
                                Se o processo seletivo não estiver encerrado.
                                Se não tiver as permissões corretas para realizar a ação.
        """
        if self.search_count(cr, uid, [('id', 'in', ids), ('state', '!=', 'analise')]):
            raise orm.except_orm(
                u'Ação não permitida',
                u'Não é possível mudar o status de inscrições já avaliadas.'
            )
        cr.execute('''
        SELECT EXISTS (
            SELECT
                insc.id
            FROM
                %(insc)s insc INNER JOIN %(ps)s ps ON (insc.processo_seletivo_id = ps.id)
            WHERE
                insc.id in (%(ids)s) AND ps.state != 'encerrado'
        );
        ''' % {
            'insc': self._table,
            'ps': self.pool.get('ud_monitoria.processo_seletivo')._table,
            'ids': str(ids).lstrip('[(').rstrip(']),').replace('L', '')
        })
        if cr.fetchone()[0]:
            raise orm.except_orm(
                u'Ação inválida',
                u'Não é possível alterar o status da inscrição enquanto o processo seletivo não estiver encerrado.'
            )
        grupos = [
            'ud_monitoria.group_ud_monitoria_orientador',
            'ud_monitoria.group_ud_monitoria_coordenador,ud_monitoria.group_ud_monitoria_administrador',
        ]
        if not self.user_has_groups(cr, uid, ','.join(grupos)):
            raise orm.except_orm(
                u'Acesso Negado!',
                u'Você não possui permissão para realizar essa ação'
            )
        for insc in self.browse(cr, uid, ids, context):
            if not self.user_has_groups(cr, uid, grupos[1]):
                if not self.user_has_groups(cr, uid, grupos[0]):
                    raise orm.except_orm(
                        u'Acesso Negado!',
                        u'Você não faz parte de nenhum grupo de segurança que permite alterar o status de inscrições.'
                    )
                elif insc.disciplina_id.orientador_id.user_id.id != uid:
                    raise orm.except_orm(
                        u'Acesso Negado!',
                        u'Você não é o orientador da disciplina da inscrição atual.'
                    )
        return self.write(cr, uid, ids, {'state': 'desclassificado'}, context)

    def acao(self, cr, uid, ids, context=None):
        """
        Apenas para servir para salvar a inscrição quando clicado em no botão.
        """
        return True

    # Ações ao atualizar campos
    def onchage_processo_seletivo(self, cr, uid, ids, ps, context=None):
        res = {'value': {'bolsas_curso_id': False, 'disciplina_id': False}}
        if ps:
            semestre = self.pool.get('ud_monitoria.processo_seletivo').read(
                cr, SUPERUSER_ID, ps, ['semestre_id'], load='_classic_write'
            )['semestre_id']
            res['domain'] = {'bolsas_curso_id': [('semestre_id', '=', semestre)]}
        return res

    def onchange_curso(self, cr, uid, ids, context=None):
        return {'value': {'disciplina_id': False}}

    def onchange_perfil_ou_bolsista(self, cr, uid, ids, perfil_id, bolsista, context=None):
        res = {'value': {'discente_id': False, 'curso_id': False, 'celular': False,
               'email': False, 'telefone_fixo': False, 'dados_bancarios_id': False}}
        if perfil_id:
            perfil_model = self.pool.get('ud.perfil')
            perfil = perfil_model.browse(cr, uid, perfil_id, context=context)
            res['value']['discente_id'] = perfil.ud_papel_id.id
            res['value']['curso_id'] = perfil.ud_cursos.id
            res['value']['celular'] = perfil.ud_papel_id.mobile_phone
            res['value']['email'] = perfil.ud_papel_id.work_email
            res['value']['telefone_fixo'] = perfil.ud_papel_id.work_phone
            if bolsista:
                if perfil.is_bolsista:
                    res['value']['bolsista'] = False
                    res['value']['dados_bancarios_id'] = False
                    res['warning'] = {
                        'title': u'Discente bolsista',
                        'message': u'Não é permitido fazer inscrição de discentes registrados como bolsista.'
                    }
        return res

    def onchange_tutoria(self, cr, uid, ids, context=None):
        return {'value': {'disciplina_id': False}}

    def onchange_pontuacoes(self, cr, uid, ids, pontuacoes, context=None):
        tipo_media = self.browse(cr, uid, ids[0]).processo_seletivo_id.tipo_media
        pontuacao_model = self.pool.get('ud_monitoria.pontuacao')
        if tipo_media == 'a':
            soma = total = 0
            for pont in pontuacoes:
                total += 1
                if pont[0] == 1:
                    soma += pont[-1]['pontuacao']
                elif pont[0] == 4:
                    soma += pontuacao_model.read(cr, uid, pont[1], ['pontuacao'], load='_classic_write')['pontuacao']
                else:
                    return {'warning': {'title': u'Ação inválida',
                                        'message': u'É permitido apenas atualzia a pontuação dos critérios avaliativos.'}}
            return {'value': {'media': total and round(soma / total, 2) or 0}}
        elif tipo_media == 'p':
            soma = pesos = 0
            for pont in pontuacoes:
                pontuacao = pontuacao_model.browse(cr, uid, pont[1])
                pesos += pontuacao.criterio_avaliativo_id.peso
                if pont[0] == 1:
                    soma += pont[-1]['pontuacao'] * pontuacao.criterio_avaliativo_id.peso
                elif pont[0] == 4:
                    soma += pontuacao.pontuacao * pontuacao.criterio_avaliativo_id.peso
                else:
                    return {'warning': {'title': u'Ação inválida',
                                        'message': u'É permitido apenas atualzia a pontuação dos critérios avaliativos.'}}
            return {'value': {'media': pesos and round(soma / pesos, 2) or 0}}
        return {}
