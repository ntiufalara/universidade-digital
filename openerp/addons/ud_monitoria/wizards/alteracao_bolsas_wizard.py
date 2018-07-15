# coding: utf-8
from openerp import SUPERUSER_ID
from openerp.osv import osv, fields, orm
from openerp.addons.ud.ud import _TIPOS_BOLSA

from ..models.util import data_hoje, DEFAULT_SERVER_DATE_FORMAT


TIPOS_BOLSA = dict(_TIPOS_BOLSA)


def get_banco(cls, cr, browse_record, usuario_id, context=None):
    """
    Busca ou cria um registro de dados bancários do núcleo para um usuário.

    :raise osv.except_osv: Caso os dados bancários pesquisados pertençam a outro usuário.
    """
    dados_bancarios_model = cls.pool.get("ud.dados.bancarios")
    args = [("banco_id", "=", browse_record.banco_id.id)]
    if browse_record.agencia_v:
        args.append(("agencia", "=", browse_record.agencia))
    if browse_record.dv_agencia_v:
        args.append(("dv_agencia", "=", browse_record.dv_agencia))
    if browse_record.conta_v:
        args.append(("conta", "=", browse_record.conta))
    if browse_record.dv_conta_v:
        args.append(("dv_conta", "=", browse_record.dv_conta))
    if browse_record.operacao_v:
        args.append(("operacao", "=", browse_record.operacao))
    dados_bancarios = dados_bancarios_model.search(cr, SUPERUSER_ID, args, context=context)
    if dados_bancarios:
        dados_bancarios = dados_bancarios_model.browse(cr, SUPERUSER_ID, dados_bancarios[0])
        if not dados_bancarios.ud_conta_id:
            return dados_bancarios.id
        elif dados_bancarios.ud_conta_id.id == usuario_id:
            return dados_bancarios.id
        raise orm.except_orm(u'Dados Bancários duplicados', u'Esses dados bancários já pertencem a outra pessoa.')
    dados = {"banco_id": browse_record.banco_id.id, "ud_conta_id": usuario_id, "agencia": browse_record.agencia,
             "dv_agencia": browse_record.dv_agencia, "conta": browse_record.conta, "dv_conta": browse_record.dv_conta,
             "operacao": browse_record.operacao}
    return dados_bancarios_model.create(cr, SUPERUSER_ID, dados, context=context)


class AdicionarBolsaWizard(osv.TransientModel):
    _name = 'ud_monitoria.bolsa_adicionar_wizard'
    _description = u'Inclusão de bolsa de monitoria para discente (UD)'

    _STATES = [
        ('n_bolsista', u'Não Bolsista'),
        ('reserva', u'Cadastro de Reserva'),
    ]

    _columns = {
        'semestre_id': fields.many2one('ud_monitoria.semestre', u'Semestre', required=True, readonly=True,
                                       domain=[('is_active', '=', True)]),
        'bolsas_curso_id': fields.many2one('ud_monitoria.bolsas_curso', u'Curso', required=True,
                                           domain="[('semestre_id', '=', semestre_id)]"),
        'disciplina_id': fields.many2one('ud_monitoria.disciplina', u'Disciplinas', required=True,
                                         domain="[('bolsas_curso_id', '=', bolsas_curso_id)]"),
        'perfil_id': fields.related('disciplina_id', 'perfil_id', type='many2one', relation='ud.perfil',
                                    string=u'SIAPE', readonly=True),
        'orientador_id': fields.related('disciplina_id', 'perfil_id', 'ud_papel_id', type='many2one',
                                        relation='ud.employee', string=u'Orientador', readonly=True),
        'bolsas': fields.integer(u'Bolsas disponíveis', help=u'Número de bolsas disponíveis para a disciplina'),
        'valor_bolsa': fields.float(u'Bolsa (R$)', required=True),
        'tutor': fields.boolean(u'Tutor?'),
        'status': fields.selection(_STATES, u'Status', required=True),
        'doc_discente_id': fields.many2one('ud_monitoria.documentos_discente', u'Discente', required=True,
                                             domain="[('disciplina_id', '=', disciplina_id), ('tutor', '=', tutor), "
                                                    "('state', '=', status)]"),
        'discente_id': fields.related('doc_discente_id', 'perfil_id', 'ud_papel_id', type='many2one', relation='ud.employee',
                                      string=u'Discente', readonly=True),
        # DADOS BANCÁRIOS
        'dados_bancarios_id': fields.many2one('ud.dados.bancarios', u'Dados Bancários',
                                              domain='[("ud_conta_id", "=", discente_id)]'),
        'banco_id': fields.many2one('ud.banco', u'Banco'),
        'agencia': fields.char(u'Agência', size=4, help=u'Número da Agência'),
        'dv_agencia': fields.char(u'DV Agência', size=2, help=u'Dígito verificador da Agência'),
        'conta': fields.char(u'Conta', size=10, help=u'Número da Conta'),
        'dv_conta': fields.char(u'DV Conta', size=1, help=u'Dígito verificador da Conta'),
        'operacao': fields.char(u'Operação', size=3, help=u'Tipo de conta'),

        'agencia_v': fields.related('banco_id', 'agencia', type='boolean', invisible=True, readonly=True),
        'dv_agencia_v': fields.related('banco_id', 'dv_agencia', type='boolean', invisible=True, readonly=True),
        'conta_v': fields.related('banco_id', 'conta', type='boolean', invisible=True, readonly=True),
        'dv_conta_v': fields.related('banco_id', 'dv_conta', type='boolean', invisible=True, readonly=True),
        'operacao_v': fields.related('banco_id', 'operacao', type='boolean', invisible=True, readonly=True),
    }

    def default_get(self, cr, uid, fields_list, context=None):
        res = super(AdicionarBolsaWizard, self).default_get(cr, uid, fields_list, context)
        res['status'] = 'n_bolsista'
        res['valor_bolsa'] = 400.
        context = context or {}
        if context.get('active_id', False):
            if context.get('active_model', False) == 'ud_monitoria.semestre':
                res['semestre_id'] = context.get('active_id')
            elif context.get('active_model', False) == 'ud_monitoria.documentos_discente':
                doc = self.pool.get('ud_monitoria.documentos_discente').browse(cr, uid, context['active_id'], context)
                res['semestre_id'] = doc.disciplina_id.semestre_id.id
                res['bolsas_curso_id'] = doc.disciplina_id.bolsas_curso_id.id
                res['disciplina_id'] = doc.disciplina_id.id
                res['tutor'] = doc.tutor
                res['status'] = doc.state
                res['doc_discente_id'] = doc.id
                res['dados_bancarios_id'] = getattr(doc.dados_bancarios_id, 'id', False)
        return res

    def view_init(self, cr, uid, fields_list, context=None):
        if context.get('active_id', False):
            if context.get('active_model', False) == 'ud_monitoria.semestre':
                semestre = self.pool.get('ud_monitoria.semestre').browse(cr, uid, context['active_id'], context)
                if not semestre.is_active:
                    raise orm.except_orm(
                        u'Semestre inativo',
                        u'Alteração indisponível enquanto o semestre correspondente estiver inativo (%s).'
                        % semestre.semestre
                    )
            elif context.get('active_model', False) == 'ud_monitoria.documentos_discente':
                doc = self.pool.get('ud_monitoria.documentos_discente').browse(cr, uid, context['active_id'], context)
                if doc.state == 'bolsista':
                    raise orm.except_orm(u'Discente bolsista', u'O discente já é bolsista.')
                elif not doc.semestre_id.is_active:
                    raise orm.except_orm(
                        u'Semestre Inativo',
                        u'Alteração indisponível enquanto o semestre correspondente estiver inativo (%s).'
                        % doc.semestre_id.semestre
                    )

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = super(AdicionarBolsaWizard, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
        if 'disciplina_id' in res['fields']:
            res['fields']['disciplina_id']['domain'] = "[('bolsas_curso_id', '=', bolsas_curso_id), ('data_final', '>=', '%s')]" % (
                data_hoje(self, cr).strftime(DEFAULT_SERVER_DATE_FORMAT)
            )
        return res

    def onchange_curso(self, cr, uid, ids, context=None):
        return {'value': {'disciplina_id': False}}

    def onchange_disciplina(self,  cr, uid, ids, disciplina, context=None):
        res = {'value': {'bolsas': 0, 'doc_discente_id': False, 'perfil_id': False, 'orientador_id': False}}
        if disciplina:
            disciplina = self.pool.get('ud_monitoria.disciplina').browse(cr, uid, disciplina, context)
            res['value']['bolsas'] = disciplina.bolsas_disponiveis
            res['value']['perfil_id'] = disciplina.perfil_id.id
            res['value']['orientador_id'] = disciplina.orientador_id.id
            if disciplina.bolsas_disponiveis < 1:
                res['warning'] = {
                    'title': u'Bolsas indisponíveis',
                    'message': u'Não há bolsas disponíveis nessa(s) disciplina(s).'
                }
        return res

    def onchange_doc_discente(self, cr, uid, ids, doc_discente_id, context=None):
        res = {'value': {'discente_id': False, 'dados_bancarios_id': False}}
        if doc_discente_id:
            res['value']['discente_id'] = self.pool.get('ud_monitoria.documentos_discente').browse(
                cr, uid, doc_discente_id, context
            ).discente_id.id
        return res

    def onchange_limpar_doc_discente(self, cr, uid, ids, context=None):
        return {'value': {'doc_discente_id': False}}

    def onchange_banco(self, cr, uid, ids, banco_id, context=None):
        if banco_id:
            banco = self.pool.get('ud.banco').read(cr, uid, banco_id, [
                'agencia', 'dv_agencia', 'conta', 'dv_conta', 'operacao'
            ], context=context, load='_classic_write')
            vals = {'agencia': False, 'dv_agencia': False, 'conta': False, 'dv_conta': False, 'operacao': False}
            vals.update({'%s_v' % dado: banco.get(dado) for dado in banco.keys()})
            return {'value': vals}
        return {'value': {'agencia_v': False, 'dv_agencia_v': False, 'conta_v': False, 'dv_conta_v': False,'operacao_v': False,
                          'agencia': False, 'dv_agencia': False, 'conta': False, 'dv_conta': False, 'operacao': False}}

    def executar_acao(self, cr, uid, ids, context=None):
        perfil_model = self.pool.get('ud.perfil')
        ocorrencia_model = self.pool.get('ud_monitoria.ocorrencia')
        for add in self.browse(cr, uid, ids, context):
            perfil = add.doc_discente_id.perfil_id
            if add.disciplina_id.bolsas_disponiveis == 0:
                raise osv.except_osv(u'Bolsas Insuficientes', u'Não há bolsas disponíveis para a(s) disciplina(s).')
            elif not add.doc_discente_id.is_active:
                raise osv.except_osv(
                    u'Registro inativo',
                    u'O registro do discente (%s - %s) não pode ser classificado como bolsista por está inativo.'
                    % (perfil.matricula, add.doc_discente_id.discente_id.name)
                )
            if perfil.is_bolsista:
                raise osv.except_osv(
                    u'Discente bolsista',
                    u'O discente "%s", sob matrícula "%s", possui bolsa do tipo "%s"'
                    % (add.doc_discente_id.discente_id.name, perfil.matricula, TIPOS_BOLSA[perfil.tipo_bolsa])
                )
            responsavel = self.pool.get('ud.employee').search(cr, SUPERUSER_ID, [('user_id', '=', uid)], limit=2)
            if not responsavel:
                raise osv.except_osv(
                    u'Registro Inexistente',
                    u'Não é possível realizar essa alteração enquanto seu login não estiver vinculado ao núcleo'
                )
            if len(responsavel) > 1:
                raise osv.except_osv(
                    u'Multiplos vínculos',
                    u'Não é possível realizar essa alteração enquanto seu login possuir multiplos vínculos no núcleo'
                )
            perfil_model.write(cr, SUPERUSER_ID, perfil.id, {
                'is_bolsista': True, 'tipo_bolsa': 'm', 'valor_bolsa': ('%.2f' % add.valor_bolsa).replace('.', ',')
            })
            if add.dados_bancarios_id:
                dados = add.dados_bancarios_id.id
            else:
                dados = get_banco(self, cr, add, add.doc_discente_id.discente_id.id, context)
            add.doc_discente_id.write({
                'state': 'bolsista',
                'dados_bancarios_id': dados
            })
            ocorrencia_model.create(cr, SUPERUSER_ID, {
                'semestre_id': add.semestre_id.id,
                'responsavel_id': responsavel[0],
                'name': u'Adição de bolsa: "%s"' % add.doc_discente_id.discente_id.name,
                'envolvidos_ids': [(4, add.doc_discente_id.discente_id.id)],
                'descricao': u'Uma bolsa de R$ %s foi vinculada para o(a) discente "%s" sob matrícula "%s".%s' % (
                    ('%.2f' % add.valor_bolsa).replace('.', ','),
                    add.doc_discente_id.discente_id.name.upper(), perfil.matricula,
                    u' Anteriormente o(a) discente estava no cadastro de reserva.'
                    if add.doc_discente_id.state == 'reserva' else ''
                )
            })
        return True


class TransferirBolsaWizard(osv.TransientModel):
    _name = 'ud_monitoria.bolsa_transferir_wizard'
    _description = u'Transferência de bolsa de monitoria (UD)'

    _STATES = [
        ('n_bolsista', u'Não Bolsista'),
        ('reserva', u'Cadastro de Reserva'),
    ]

    _columns = {
        'semestre_id': fields.many2one('ud_monitoria.semestre', u'Semestre', required=True, readonly=True,
                                       domain=[('is_active', '=', True)]),
        # Bolsa Origem
        'bolsas_curso_id_de': fields.many2one('ud_monitoria.bolsas_curso', u'Curso', required=True,
                                           domain="[('semestre_id', '=', semestre_id)]"),
        'disciplina_id_de': fields.many2one('ud_monitoria.disciplina', u'Disciplinas', required=True,
                                         domain="[('bolsas_curso_id', '=', bolsas_curso_id_de)]"),
        'perfil_id_de': fields.related('disciplina_id_de', 'perfil_id', type='many2one', relation='ud.perfil',
                                    string=u'SIAPE', readonly=True),
        'orientador_id_de': fields.related('disciplina_id_de', 'perfil_id', 'ud_papel_id', type='many2one',
                                        relation='ud.employee', string=u'Orientador', readonly=True),
        'tutor_de': fields.boolean(u'Tutor?'),
        'doc_discente_id_de': fields.many2one('ud_monitoria.documentos_discente', u'Discente', required=True,
                                           domain="[('disciplina_id', '=', disciplina_id_de),"
                                                  "('tutor', '=', tutor_de), ('state', '=', 'bolsista')]"),
        'valor_bolsa': fields.related('doc_discente_id_de', 'perfil_id', 'valor_bolsa', type='char',
                                      string=u'Bolsa (R$)', readonly=True),
        # Bolsa Destino
        'bolsas_curso_id_para': fields.many2one('ud_monitoria.bolsas_curso', u'Curso', required=True,
                                         domain="[('semestre_id', '=', semestre_id)]"),
        'disciplina_id_para': fields.many2one('ud_monitoria.disciplina', u'Disciplinas', required=True,
                                         domain="[('bolsas_curso_id', '=', bolsas_curso_id_para)]"),
        'perfil_id_para': fields.related('disciplina_id_para', 'perfil_id', type='many2one', relation='ud.perfil',
                                       string=u'SIAPE', readonly=True),
        'orientador_id_para': fields.related('disciplina_id_para', 'perfil_id', 'ud_papel_id', type='many2one',
                                           relation='ud.employee', string=u'Orientador', readonly=True),
        'tutor_para': fields.boolean(u'Tutor?'),
        'status_para': fields.selection(_STATES, u'Status', required=True),
        'doc_discente_id_para': fields.many2one('ud_monitoria.documentos_discente', u'Discente', required=True,
                                                domain="[('state', '=', status_para), ('tutor', '=', tutor_para),"
                                                       "('disciplina_id', '=', disciplina_id_para)]"),
        # Campo usado para filtrar os dados bancários
        'discente_id': fields.related('doc_discente_id_para', 'perfil_id', 'ud_papel_id', type='many2one',
                                      relation='ud.employee', string=u'Discente', readonly=True),
        # DADOS BANCÁRIOS
        'dados_bancarios_id': fields.many2one('ud.dados.bancarios', u'Dados Bancários', domain='[("ud_conta_id", "=", discente_id)]'),
        'banco_id': fields.many2one('ud.banco', u'Banco'),
        'agencia': fields.char(u'Agência', size=4, help=u'Número da Agência'),
        'dv_agencia': fields.char(u'DV Agência', size=2, help=u'Dígito verificador da Agência'),
        'conta': fields.char(u'Conta', size=10, help=u'Número da Conta'),
        'dv_conta': fields.char(u'DV Conta', size=1, help=u'Dígito verificador da Conta'),
        'operacao': fields.char(u'Operação', size=3, help=u'Tipo de conta'),

        'agencia_v': fields.related('banco_id', 'agencia', type='boolean', invisible=True, readonly=True),
        'dv_agencia_v': fields.related('banco_id', 'dv_agencia', type='boolean', invisible=True, readonly=True),
        'conta_v': fields.related('banco_id', 'conta', type='boolean', invisible=True, readonly=True),
        'dv_conta_v': fields.related('banco_id', 'dv_conta', type='boolean', invisible=True, readonly=True),
        'operacao_v': fields.related('banco_id', 'operacao', type='boolean', invisible=True, readonly=True),
    }

    def default_get(self, cr, uid, fields_list, context=None):
        res = super(TransferirBolsaWizard, self).default_get(cr, uid, fields_list, context)
        context = context or {}
        if context.get('active_id', False):
            if context.get('active_model', False) == 'ud_monitoria.semestre':
                res['semestre_id'] = context.get('active_id')
            elif context.get('active_model', False) == 'ud_monitoria.documentos_discente':
                doc = self.pool.get("ud_monitoria.documentos_discente").browse(cr, uid, context.get("active_id"), context)
                if doc.state != "bolsista":
                    raise orm.except_orm(
                        u'Discente não bolsista',
                        u'Para transferir uma bolsa, é necessário que o discente de origem seja bolsista.'
                    )
                res["doc_discente_id_de"] = doc.id
                res["disciplina_id_de"] = doc.disciplina_id.id
                res["perfil_id_de"] = doc.disciplina_id.perfil_id.id
                res["orientador_id_de"] = doc.disciplina_id.orientador_id.id
                res["bolsas_curso_id_de"] = doc.disciplina_id.bolsas_curso_id.id
                res["semestre_id"] = doc.semestre_id.id
                res["valor_bolsa"] = doc.perfil_id.valor_bolsa
                res["tutor_de"] = doc.tutor
                res["status_de"] = doc.state
        return res

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = super(TransferirBolsaWizard, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
        hoje = data_hoje(self, cr).strftime(DEFAULT_SERVER_DATE_FORMAT)
        if 'disciplina_id_de' in res['fields']:
            res['fields']['disciplina_id_de']['domain'] = "[('bolsas_curso_id', '=', bolsas_curso_id_de), ('data_final', '>=', '%(hj)s')]" % {
                'hj': hoje
            }
        if 'disciplina_id_para' in res['fields']:
            res['fields']['disciplina_id_para']['domain'] = "[('bolsas_curso_id', '=', bolsas_curso_id_para), ('data_final', '>=', '%(hj)s')]" % {
                'hj': hoje
            }
        return res

    def onchange_curso(self, cr, uid, ids, comp, context=None):
        return {"value": {"disciplina_id_" + comp: False}}

    def onchange_disciplina(self,  cr, uid, ids, comp, disc, context=None):
        res = {'value': {'doc_discente_id_' + comp: False, 'perfil_id_' + comp: False, 'orientador_id_' + comp: False}}
        if disc:
            disc = self.pool.get('ud_monitoria.disciplina').browse(cr, uid, disc)
            res['value']['perfil_id_' + comp] = disc.perfil_id.id
            res['value']['orientador_id_' + comp] = disc.orientador_id.id
        elif comp == 'de':
            res['value']['valor_bolsa'] = False
        return res

    def onchange_discente(self, cr, uid, ids, comp, doc, context=None):
        if doc:
            doc = self.pool.get('ud_monitoria.documentos_discente').browse(cr, uid, doc)
            if comp == 'de':
                return {'value': {'valor_bolsa': doc.perfil_id.valor_bolsa}}
            else:
                return {'value': {'dados_bancarios_id': getattr(doc.dados_bancarios_id, 'id', False),
                                  'discente_id': doc.discente_id.id}}
        elif comp == 'de':
            return {'value': {'valor_bolsa': False}}
        else:
            return {'value': {'dados_bancarios_id': False, 'discente_id': False}}

    def onchange_limpa_discente(self, cr, uid, ids, comp, context=None):
        return {'value': {'doc_discente_id_' + comp: False}}

    def onchange_banco(self, cr, uid, ids, banco_id, context=None):
        if banco_id:
            banco = self.pool.get('ud.banco').read(cr, uid, banco_id, [
                'agencia', 'dv_agencia', 'conta', 'dv_conta', 'operacao'
            ], context=context, load='_classic_write')
            vals = {'agencia': False, 'dv_agencia': False, 'conta': False, 'dv_conta': False, 'operacao': False}
            vals.update({'%s_v' % dado: banco.get(dado) for dado in banco.keys()})
            return {'value': vals}
        return {'value': {'agencia_v': False, 'dv_agencia_v': False, 'conta_v': False, 'dv_conta_v': False,'operacao_v': False,
                          'agencia': False, 'dv_agencia': False, 'conta': False, 'dv_conta': False, 'operacao': False}}

    def executar_acao(self, cr, uid, ids, context=None):
        perfil_model = self.pool.get('ud.perfil')
        for transf in self.browse(cr, uid, ids, context):
            if transf.doc_discente_id_para.perfil_id.is_bolsista:
                raise osv.except_osv(
                    u'Discente bolsista',
                    u'O(a) discente "{}", sob matrícula "{}", possui bolsa do tipo "{}"'.format(
                        transf.doc_discente_id_para.discente_id.name, transf.doc_discente_id_para.perfil_id.matricula,
                        TIPOS_BOLSA[transf.doc_discente_id_para.perfil_id.tipo_bolsa]
                    )
                )
            responsavel = self.pool.get('ud.employee').search(cr, SUPERUSER_ID, [('user_id', '=', uid)], limit=2)
            if not responsavel:
                raise osv.except_osv(
                    u'Registro Inexistente',
                    u'Não é possível realizar essa alteração enquanto seu login não estiver vinculado ao núcleo'
                )
            if len(responsavel) > 1:
                raise osv.except_osv(
                    u'Multiplos vínculos',
                    u'Não é possível realizar essa alteração enquanto seu login possuir multiplos vínculos no núcleo'
                )
            perfil_model.write(cr, SUPERUSER_ID, transf.doc_discente_id_para.perfil_id.id, {
                'is_bolsista': True, 'tipo_bolsa': 'm', 'valor_bolsa': transf.doc_discente_id_de.perfil_id.valor_bolsa
            })
            perfil_model.write(cr, SUPERUSER_ID, transf.doc_discente_id_de.perfil_id.id, {
                'is_bolsista': False, 'tipo_bolsa': False, 'valor_bolsa': False
            })
            if transf.disciplina_id_de.colaboradores - len(transf.disciplina_id_de.n_bolsista_ids) < 1:
                transf.disciplina_id_de.write({'colaboradores': transf.disciplina_id_de.colaboradores + 1})
            transf.doc_discente_id_de.write({'state': 'n_bolsista'})
            if transf.bolsas_curso_id_de.id != transf.bolsas_curso_id_para.id:
                transf.bolsas_curso_id_de.write({
                    'bolsas': transf.bolsas_curso_id_de.bolsas - 1,
                    'disciplina_ids': [
                        (1, transf.disciplina_id_de.id, {
                            'bolsistas': transf.disciplina_id_de.bolsistas - 1,
                            'colaboradores': transf.disciplina_id_de.colaboradores or 1
                        })
                    ]
                })
                transf.bolsas_curso_id_para.write({
                    'bolsas': transf.bolsas_curso_id_para.bolsas + 1,
                    'disciplina_ids': [
                        (1, transf.disciplina_id_para.id, {'bolsistas': transf.disciplina_id_para.bolsistas + 1})
                    ]
                })
            elif transf.disciplina_id_de.id != transf.disciplina_id_para.id:
                transf.disciplina_id_de.write({
                    'bolsistas': transf.disciplina_id_de.bolsistas - 1,
                    'colaboradores': transf.disciplina_id_de.colaboradores or 1
                })
                transf.disciplina_id_para.write({'bolsistas': transf.disciplina_id_para.bolsistas + 1})
            if transf.doc_discente_id_para.state == 'reserva':
                reserva = u' Anteriormente esse(a) discente estava no cadastro de reserva.'
            else:
                reserva = ''
            if transf.dados_bancarios_id:
                dados_bancarios = transf.dados_bancarios_id.id
            else:
                dados_bancarios = get_banco(self, cr, transf, transf.doc_discente_id_para.discente_id.id, context)
            transf.doc_discente_id_para.write({'state': 'bolsista', 'dados_bancarios_id': dados_bancarios})
            transf.semestre_id.write({
                'ocorrencias_ids': [
                    (0, 0, {
                        'responsavel_id': responsavel[0],
                        'name': u'Transferência de bolsa',
                        'envolvidos_ids': [(4, transf.doc_discente_id_de.discente_id.id),
                                           (4, transf.doc_discente_id_para.discente_id.id)],
                        'descricao': u'Transferência de bolsa no valor de R$ %(valor)s do(a) discente '
                                     u'"%(discente_de)s", sob matrícula %(matricula_de)s, para o(a) discente '
                                     u'"%(discente_para)s", sob matrícula "%(matricula_para)s".%(pos)s' % {
                                         'valor': transf.doc_discente_id_de.perfil_id.valor_bolsa,
                                         'discente_de': transf.doc_discente_id_de.discente_id.name.upper(),
                                         'matricula_de': transf.doc_discente_id_de.perfil_id.matricula,
                                         'discente_para': transf.doc_discente_id_para.discente_id.name.upper(),
                                         'matricula_para': transf.doc_discente_id_para.perfil_id.matricula,
                                         'pos': reserva
                                     }
                    })
                ]
            })
        return True


class RemoverBolsaWizard(osv.TransientModel):
    _name = "ud_monitoria.bolsa_remover_wizard"
    _description = u"Remoção de bolsa de discente (UD)"

    _columns = {
        'semestre_id': fields.many2one('ud_monitoria.semestre', u'Semestre', required=True, readonly=True,
                                       domain=[('is_active', '=', True)]),
        'bolsas_curso_id': fields.many2one('ud_monitoria.bolsas_curso', u'Curso', required=True,
                                           domain="[('semestre_id', '=', semestre_id)]"),
        'disciplina_id': fields.many2one('ud_monitoria.disciplina', u'Disciplinas', required=True,
                                         domain="[('bolsas_curso_id', '=', bolsas_curso_id)]"),
        'perfil_id': fields.related('disciplina_id', 'perfil_id', type='many2one', relation='ud.perfil',
                                    string=u'SIAPE', readonly=True),
        'orientador_id': fields.related('disciplina_id', 'perfil_id', 'ud_papel_id', type='many2one',
                                        relation='ud.employee', string=u'Orientador', readonly=True),
        'vagas': fields.integer(u'Vagas', readonly=True, help=u'Número de vagas disponíveis.'),
        "tutor": fields.boolean(u"Tutor?"),
        "doc_discente_id": fields.many2one("ud_monitoria.documentos_discente", u"Discente", required=True,
                                             domain="[('disciplina_id', '=', disciplina_id), ('tutor', '=', tutor), "
                                                    "('state', '=', 'bolsista')]"),
    }

    def default_get(self, cr, uid, fields_list, context=None):
        res = super(RemoverBolsaWizard, self).default_get(cr, uid, fields_list, context)
        context = context or {}
        if context.get("active_id", False):
            if context.get("active_model", False) == "ud_monitoria.semestre":
                res["semestre_id"] = context.get("active_id")
            elif context.get("active_model", False) == "ud_monitoria.documentos_discente":
                doc = self.pool.get("ud_monitoria.documentos_discente").browse(cr, uid, context.get("active_id"), context)
                if doc.state != "bolsista":
                    raise osv.except_osv(u"Discente não bolsista", u"O discente não é bolsista")
                elif not doc.is_active:
                    raise osv.except_osv(u"Documento do discente inativo",
                                         u"Não é possível realizar essa ação para documentos inativos")
                res["doc_discente_id"] = doc.id
                res["semestre_id"] = doc.semestre_id.id
                res["disciplina_id"] = doc.disciplina_id.id
                res["bolsas_curso_id"] = doc.disciplina_id.bolsas_curso_id.id
                res["tutor"] = doc.tutor
        return res

    def view_init(self, cr, uid, fields_list, context=None):
        if context.get('active_id', False):
            if context.get('active_model', False) == 'ud_monitoria.semestre':
                semestre = self.pool.get('ud_monitoria.semestre').browse(cr, uid, context['active_id'], context)
                if not semestre.is_active:
                    raise orm.except_orm(
                        u'Semestre inativo',
                        u'Alteração indisponível enquanto o semestre correspondente estiver inativo (%s).'
                        % semestre.semestre
                    )
            elif context.get('active_model', False) == 'ud_monitoria.documentos_discente':
                doc = self.pool.get('ud_monitoria.documentos_discente').browse(cr, uid, context['active_id'], context)
                if doc.state != 'bolsista':
                    raise orm.except_orm(u'Discente não bolsista',
                                         u'É necessário que o discente seja bolsista para realizar essa ação.')
                elif not doc.semestre_id.is_active:
                    raise orm.except_orm(
                        u'Semestre Inativo',
                        u'Alteração indisponível enquanto o semestre correspondente estiver inativo (%s).'
                        % doc.semestre_id.semestre
                    )

    def onchange_curso(self, cr, uid, ids, context=None):
        return {'value': {'disciplina_id': False}}

    def onchange_disciplina(self,  cr, uid, ids, disciplina, context=None):
        res = {'value': {'bolsas': 0, 'doc_discente_id': False, 'perfil_id': False, 'orientador_id': False}}
        if disciplina:
            disciplina = self.pool.get('ud_monitoria.disciplina').browse(cr, uid, disciplina, context)
            res['value']['vagas'] = disciplina.colaboradores - len(disciplina.n_bolsista_ids)
            res['value']['perfil_id'] = disciplina.perfil_id.id
            res['value']['orientador_id'] = disciplina.orientador_id.id
            if res['value']['vagas'] < 1:
                res['warning'] = {
                    'title': u'Vaga indisponível',
                    'message': u'Não há vagas disponíveis para colaboradores nessa(s) disciplina(s).'
                }
        return res

    def onchange_tutor(self,  cr, uid, ids, context=None):
        return {'value': {'doc_discente_id': False}}

    def executar_acao(self, cr, uid, ids, context=None):
        perfil_model = self.pool.get('ud.perfil')
        pessoa_model = self.pool.get('ud.employee')
        for rem in self.browse(cr, uid, ids, context):
            if rem.doc_discente_id.perfil_id.is_bolsista and rem.doc_discente_id.perfil_id.tipo_bolsa != 'm':
                raise orm.except_orm(
                    u'Categoria de bolsa',
                    u'A categoria de bolsa do discente "%s" sob matrícula "%s" não é pertencente à monitoria: "%s"'
                    % (rem.doc_discente_id.discente_id.name, rem.doc_discente_id.perfil_id.matricula,
                       TIPOS_BOLSA[rem.doc_discente_id.perfil_id.tipo_bolsa])
                )
            responsavel = pessoa_model.search(cr, SUPERUSER_ID, [('user_id', '=', uid)], limit=2)
            if not responsavel:
                raise osv.except_osv(
                    u'Registro Inexistente',
                    u'Não é possível realizar essa alteração enquanto seu login não estiver vinculado ao núcleo'
                )
            if len(responsavel) > 1:
                raise osv.except_osv(
                    u'Multiplos vínculos',
                    u'Não é possível realizar essa alteração enquanto seu login possuir multiplos vínculos no núcleo'
                )
            perfil_model.write(cr, SUPERUSER_ID, rem.doc_discente_id.perfil_id.id, {
                'is_bolsista': False, 'tipo_bolsa': False, 'valor_bolsa': False
            })
            rem.doc_discente_id.write({'state': 'n_bolsista'})
            self.pool.get('ud_monitoria.ocorrencia').create(cr, SUPERUSER_ID, {
                'semestre_id': rem.semestre_id.id,
                'responsavel_id': responsavel[0],
                'name': u'Remoção de bolsa: "%s"' % rem.doc_discente_id.discente_id.name,
                'envolvidos_ids': [(4, rem.doc_discente_id.discente_id.id)],
                'descricao': u'A bolsa do discente "%s" sob matrícula "%s" foi removida.' % (
                    rem.doc_discente_id.discente_id.name.upper(), rem.doc_discente_id.perfil_id.matricula
                )
            })
        return True
