# coding: utf-8
"""
Criado em 16 de mai de 2016

@author: cloves
"""
from openerp import SUPERUSER_ID
from openerp.osv import osv, fields


class InscricaoWizard(osv.TransientModel):
    _name = "ud_monitoria.inscricao_wizard"
    _description = u"Inscrição (Wizard): Processos Seletivos (UD)"
    _MODALIDADE = [("monitor", u"Monitoria"), ("tutor", u"Tutoria")]
    _TURNO = [("m", u"Matutino"), ("v", u"Vespertino"), ("n", u"Noturno")]
    _columns = {
        "perfil_id": fields.many2one("ud.perfil", u"Matrícula", ondelete="cascade", domain=[("tipo", "=", "a")], required=True),
        "discente_id": fields.related("perfil_id", "ud_papel_id", type="many2one", relation="ud.employee", string=u"Discente", readonly=True),
        "celular": fields.char(u"Celular", size=15),
        "whatsapp": fields.char(u"WhatsApp", size=15, required=True),
        "email": fields.char(u"E-mail", size=240),
        "controle": fields.char(u"Controle"),

        "nome_cpf": fields.char(u"Nome CPF"),
        "nome_identidade": fields.char(u"Nome Identidade"),
        "nome_hist_analitico": fields.char(u"Nome Histórico Analítico"),
        'nome_certidao_vinculo': fields.char(u'Arquivo Certidão de Vínculo', required=True),
        "cpf": fields.binary(u"CPF"),
        "identidade": fields.binary(u"RG"),
        "hist_analitico": fields.binary(u"Hist. Analítico"),
        'certidao_vinculo': fields.binary(u'Certidão de Vínculo', required=True),
        "processo_seletivo_id": fields.many2one("ud_monitoria.processo_seletivo", u"Processo Seletivo",
                                                ondelete="cascade", domain="[('state', '=', 'andamento')]"),
        "modalidade": fields.selection(_MODALIDADE, u"Modalidade"),
        "turno": fields.selection(_TURNO, u"Turno"),
        "bolsista": fields.boolean(u"Bolsista"),
        "disciplinas_ids": fields.many2many('ud_monitoria.disciplina_ps', "ud_monitoria_disciplina_ps_inscricao_wizard_rel",
                                            "inscricao_id", "disciplina_id", string=u"Disciplinas",
                                            domain="[('processo_seletivo_id', '=', processo_seletivo_id)]"),
        # DADOS BANCÁRIOS
        "banco_id": fields.many2one("ud.banco", u"Banco", ondelete="restrict"),
        "agencia": fields.char(u"Agência", size=4, help=u"Número da Agência"),
        "dv_agencia": fields.char(u"DV Agência", size=2, help=u"Dígito verificador da Agência"),
        "conta": fields.char(u"Conta", size=10, help=u"Número da Conta"),
        "dv_conta": fields.char(u"DV Conta", size=1, help=u"Dígito verificador da Conta"),
        "operacao": fields.char(u"Operação", size=3, help=u"Tipo de conta"),

        "agencia_v": fields.related("banco_id", "agencia", type="boolean", invisible=True, readonly=True),
        "dv_agencia_v": fields.related("banco_id", "dv_agencia", type="boolean", invisible=True, readonly=True),
        "conta_v": fields.related("banco_id", "conta", type="boolean", invisible=True, readonly=True),
        "dv_conta_v": fields.related("banco_id", "dv_conta", type="boolean", invisible=True, readonly=True),
        "operacao_v": fields.related("banco_id", "operacao", type="boolean", invisible=True, readonly=True),
    }

    # Método Sobrescrito
    def default_get(self, cr, uid, fields_list, context=None):
        res = super(InscricaoWizard, self).default_get(cr, uid, fields_list, context=context)
        context = context or {}
        if context.get("active_model", False) == "ud_monitoria.processo_seletivo" and context.get("active_id", False):
            if self.pool.get("ud_monitoria.processo_seletivo").browse(cr, uid, context.get("active_id", False)).state == "andamento":
                res["processo_seletivo_id"] = context.get("active_id")
        return res

    # Funções de atualização ao alterar valor de campos no formulário
    def onchange_perfil(self, cr, uid, ids, perfil_id, bolsista, context=None):
        res = {}
        if perfil_id:
            perfil_model = self.pool.get('ud.perfil')
            perfil = perfil_model.browse(cr, uid, perfil_id, context=context)
            res['value'] = {'discente_id': perfil.ud_papel_id.id, 'celular': perfil.ud_papel_id.mobile_phone,
                            'email': perfil.ud_papel_id.work_email, 'controle': ''}
            if not perfil.ud_papel_id.mobile_phone:
                res['value']['controle'] += 'c'
            if not perfil.ud_papel_id.work_email:
                res['value']['controle'] += 'e'
            if bolsista:
                if perfil.is_bolsista:
                        res['value']['bolsista'] = False
                        res['warning'] = {
                            'title': u'Discente bolsista',
                            'message': u'Não é permitido fazer inscrição de discentes registrados como bolsista.'
                        }
        return res

    def onchange_bolsista(self, cr, uid, ids, perfil_id, discente_id, bolsista, context=None):
        if perfil_id and discente_id and bolsista:
            perfil_model = self.pool.get('ud.perfil')
            if perfil_model.read(cr, uid, perfil_id, ['is_bolsista'], context=context, load='_classic_write')['is_bolsista']:
                return {'value': {'bolsista': False},
                        'warning': {'title': u'Discente bolsista',
                                    'message': u'Não é permitido fazer inscrição de discentes bolsistas como bolsista.'}}
        elif not bolsista:
            return {'value': {'banco_id': False}}
        return {}

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

    def onchange_mod_disc(self, cr, uid, ids, modalidade, disciplinas_ids, context=None):
        res = {}
        if modalidade == 'monitor':
            res['domain'] = {'disciplinas_ids': []}
            if disciplinas_ids and len(disciplinas_ids[0][2]) > 1:
                res['value'] = {'disciplinas_ids': [disciplinas_ids[0][2][0]]}
                res['warning'] = {'title': u'Alerta',
                                  'message': u'É permitido selecionar somente 1 disciplina para "Monitoria".'}
        elif modalidade == 'tutor':
            discs_ids = self.pool.get('ud.disciplina').search(cr, SUPERUSER_ID, [('periodo', 'in', [1, 2])])
            res['domain'] = {'disciplinas_ids': [('disciplina_id', 'in', discs_ids)]}
            if disciplinas_ids:
                if len(disciplinas_ids[0][2]) > 3:
                    res['warning'] = {'title': u'Alerta',
                                      'message': u'É permitido selecionar no máximo 3 disciplinas para "Tutoria".'}
                disciplinas_ids = self.pool.get('ud_monitoria.disciplina_ps').search(
                    cr, uid, [('id', 'in', disciplinas_ids[0][2]), ('disciplina_id', 'in', discs_ids)], limit=3
                )
                res['value'] = {'disciplinas_ids': disciplinas_ids}
        elif not modalidade:
            res['domain'] = {'disciplinas_ids': [('id', '=', False)]}
            res['value'] = {'disciplinas_ids': []}
        return res

    def onchange_processo_seletivo(self, cr, uid, ids, context=None):
        return {"value": {"disciplinas_ids": []}}

    # Método auxiliar
    def _get_banco(self, cr, inscricao, context=None):
        """
        Busca um registro bancário da pessoa relacionada à inscrição. Se existir, retorna o registro. Se não, verifica
        se há outros, se não houver, cria um novo vinculado à pessoa. Se não, uma excessão é lançada.

        :return: ID dos dados bancários.
        """
        dados_bancarios_model = self.pool.get("ud.dados.bancarios")
        args = [("banco_id", "=", inscricao.banco_id.id)]
        if inscricao.agencia_v:
            args.append(("agencia", "=", inscricao.agencia))
        if inscricao.dv_agencia_v:
            args.append(("dv_agencia", "=", inscricao.dv_agencia))
        if inscricao.conta_v:
            args.append(("conta", "=", inscricao.conta))
        if inscricao.dv_conta_v:
            args.append(("dv_conta", "=", inscricao.dv_conta))
        if inscricao.operacao_v:
            args.append(("operacao", "=", inscricao.operacao))
        dados_bancarios = dados_bancarios_model.search(cr, SUPERUSER_ID, args, context=context)
        if dados_bancarios:
            dados_bancarios = dados_bancarios_model.browse(cr, SUPERUSER_ID, dados_bancarios[0])
            if not dados_bancarios.ud_conta_id:
                return dados_bancarios.id
            elif dados_bancarios.ud_conta_id.id == inscricao.discente_id.id:
                return dados_bancarios.id
            raise osv.except_osv(u"Dados Bancários duplicados", u"Não é permitido duplicar dados bancários!")
        dados = {"banco_id": inscricao.banco_id.id, "agencia": inscricao.agencia, "dv_agencia": inscricao.dv_agencia,
                 "conta": inscricao.conta, "dv_conta": inscricao.dv_conta, "operacao": inscricao.operacao,
                 "ud_conta_id": inscricao.discente_id.id}
        return dados_bancarios_model.create(cr, SUPERUSER_ID, dados, context=context)

    # Método vinculado ao botão de inscrição
    def botao_inscrever(self, cr, uid, ids, context=None):
        inscricao_model = self.pool.get("ud_monitoria.inscricao")
        perfil_model = self.pool.get("ud.perfil")
        pessoa_model = self.pool.get("ud.employee")
        res_id = False
        continua = True  # Utilizado para definir se a inscrição, se será redirecionado para visualizá-la.
        for inscricao in self.browse(cr, uid, ids, context=context):
            dados_bancarios_id = False
            pessoa_dados = {}
            if continua and getattr(inscricao.perfil_id.ud_papel_id.user_id, 'id', None) != uid:
                continua = False
            if not inscricao.perfil_id.ud_papel_id.mobile_phone and inscricao.celular and inscricao.controle in ["c", "ce"]:
                pessoa_dados["mobile_phone"] = inscricao.celular
            if not inscricao.perfil_id.ud_papel_id.work_email and inscricao.email and inscricao.controle in ["e", "ce"]:
                pessoa_dados["work_email"] = inscricao.email
            if pessoa_dados:
                inscricao.perfil_id.ud_papel_id.write(pessoa_dados)
            if inscricao.banco_id:
                dados_bancarios_id = self._get_banco(cr, inscricao, context)
            pontuacoes = [(0, 0, {"disciplina_id": disc.id,
                                  "pontuacoes_ids": [(0, 0, {"criterio_avaliativo_id": crit.id})
                                                     for crit in inscricao.processo_seletivo_id.criterios_avaliativos_ids]})
                           for disc in inscricao.disciplinas_ids]
            dados = {"perfil_id": inscricao.perfil_id.id,
                     'whatsapp': inscricao.whatsapp,
                     "cpf_nome": inscricao.nome_cpf, "cpf": inscricao.cpf,
                     "identidade_nome": inscricao.nome_identidade, "identidade": inscricao.identidade,
                     "hist_analitico_nome": inscricao.nome_hist_analitico, "hist_analitico": inscricao.hist_analitico,
                     "certidao_vinculo_nome": inscricao.nome_certidao_vinculo, "certidao_vinculo": inscricao.certidao_vinculo,
                     "processo_seletivo_id": inscricao.processo_seletivo_id.id,
                     "modalidade": inscricao.modalidade, "turno": inscricao.turno, "bolsista": inscricao.bolsista,
                     "disciplinas_ids": [(6, 0, [disc.id for disc in inscricao.disciplinas_ids])],
                     "dados_bancarios_id": dados_bancarios_id, "state": "analise",
                     "pontuacoes_ids": pontuacoes}
            res_id = inscricao_model.create(cr, SUPERUSER_ID, dados, context=context)
        if continua or self.user_has_groups(cr, uid, "ud_monitoria.group_ud_monitoria_coordenador,ud_monitoria.group_ud_monitoria_administrador,ud_monitoria.group_ud_monitoria_coord_disciplina"):
            obj_model = self.pool.get('ir.model.data')
            form_id = obj_model.get_object_reference(cr, uid, "ud_monitoria", "ud_monitoria_inscricao_form")[1]
            return {
                "name": u"Gerenciamento de Inscrições",
                "view_type": "form",
                "view_mode": "form",
                "res_model": "ud_monitoria.inscricao",
                "view_id": form_id,
                # "view_id": False,
                "type": "ir.actions.act_window",
                "nodestroy": True,
                "res_id": res_id or False,
                "target": "current",
            }
        return True
