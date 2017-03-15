# coding: utf-8
'''
Criado em 16 de mai de 2016

@author: cloves
'''

from openerp import SUPERUSER_ID
from openerp.osv import osv, fields


class InscricaoWizard(osv.TransientModel):
    _name = "ud.monitoria.inscricao.wizard"
    _description = u"Wizard para inscrição de Processos Seletivos"
    
    _MODALIDADE = [("monitor", u"Monitoria"), ("tutor", u"Tutoria")]
    
    _TURNO = [("m", u"Matutino"), ("v", u"Vespertino"), ("n", u"Noturno")]
    
    _columns = {
        "matricula": fields.char(u"Matrícula", size=15),
        "perfil_id": fields.many2one("ud.perfil", u"Matrícula", ondelete="cascade", domain=[("tipo", "=", "a")], required=True),
        "discente_id": fields.related("perfil_id", "ud_papel_id", type="many2one", relation="ud.employee",
                                      string=u"Discente", readonly=True),
        "celular": fields.char(u"Celular", size=32),
        "email": fields.char(u"E-mail", size=240),
        "controle": fields.char(u"Controle"),
        
        "nome_cpf": fields.char(u"Nome CPF"),
        "nome_identidade": fields.char(u"Nome Identidade"),
        "nome_hist_analitico": fields.char(u"Nome Histórico Analítico"),
        "cpf": fields.binary(u"CPF", required=True),
        "identidade": fields.binary(u"RG", required=True),
        "hist_analitico": fields.binary(u"Hist. Analítico", required=True),
        "processo_seletivo_id": fields.many2one("ud.monitoria.processo.seletivo", u"Processo Seletivo", required=True,
                                                ondelete="cascade", domain="[('state', '=', 'andamento')]"),
        "modalidade": fields.selection(_MODALIDADE, u"Modalidade", required=True),
        "turno": fields.selection(_TURNO, u"Turno", required=True),
        "bolsista": fields.boolean(u"Bolsista"),
        "disciplinas_ids": fields.many2many("ud.monitoria.disciplina", "ud_monitoria_disciplina_inscricao_wizard_rel",
                                            "inscricao_id", "disciplina_id", string=u"Disciplinas", required=True,
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
    
    def default_get(self, cr, uid, fields_list, context=None):
        res = super(InscricaoWizard, self).default_get(cr, uid, fields_list, context=context)
        context = context or {}
        if context.get("active_model", False) == "ud.monitoria.processo.seletivo" and context.get("active_id", False):
            if self.pool.get("ud.monitoria.processo.seletivo").browse(cr, uid, context.get("active_id", False)).state == "andamento":
                res["processo_seletivo_id"] = context.get("active_id")
        return res

    def onchange_perfil(self, cr, uid, ids, perfil_id, bolsista, context=None):
        res = {}
        if perfil_id:
            perfil_model = self.pool.get("ud.perfil")
            perfil = perfil_model.browse(cr, uid, perfil_id, context=context)
            res = {"value": {"discente_id": perfil.ud_papel_id.id, "celular": perfil.ud_papel_id.mobile_phone,
                             "email": perfil.ud_papel_id.work_email, "controle": ""}}
            if not perfil.ud_papel_id.mobile_phone:
                res["value"]["controle"] += "c"
            if not perfil.ud_papel_id.work_email:
                res["value"]["controle"] += "e"
            if bolsista:
                if perfil.is_bolsista:
                        res["value"]["bolsista"] = False
                        res["warning"] = {
                            "title": u"Discente bolsista",
                            "message": u"Não é permitido fazer inscrição de discentes registrados como bolsista."
                        }
        return res
    
    def onchange_bolsista(self, cr, uid, ids, perfil_id, discente_id, bolsista, context=None):
        if perfil_id and discente_id and bolsista:
            perfil_model = self.pool.get("ud.perfil")
            if perfil_model.read(cr, uid, perfil_id, ["is_bolsista"], context=context, load="_classic_write")["is_bolsista"]:
                return {"value": {"bolsista": False},
                        "warning": {"title": u"Discente bolsista",
                                    "message": u"Não é permitido fazer inscrição de discentes bolsistas como bolsista."}}
        elif not bolsista:
            return {"value": {"banco_id": False}}
        return {}
    
    def onchange_banco(self, cr, uid, ids, banco_id, context=None):
        if banco_id:
            banco = self.pool.get("ud.banco").read(cr, uid, banco_id, [
                "agencia", "dv_agencia", "conta", "dv_conta", "operacao"
            ], context=context, load="_classic_write")
            vals = {"agencia": False, "dv_agencia": False, "conta": False, "dv_conta": False, "operacao": False}
            vals.update({"%s_v" % dado: banco.get(dado) for dado in banco.keys()})
            return {"value": vals}
        return {"value": {"agencia_v": False, "dv_agencia_v": False, "conta_v": False, "dv_conta_v": False,"operacao_v": False,
                          "agencia": False, "dv_agencia": False, "conta": False, "dv_conta": False, "operacao": False}}
    
    def onchange_mod_disc(self, cr, uid, ids, modalidade, disciplinas_ids, context=None):
        if disciplinas_ids:
            if modalidade == "monitor" and len(disciplinas_ids[0][2]) > 1:
                return {"value": {"disciplinas_ids": [disciplinas_ids[0][2][0]]},
                        "warning": {"title": u"Alerta",
                                    "message": u"É permitido selecionar somente 1 disciplina para \"Monitoria\"."}}
            elif modalidade == "tutor" and len(disciplinas_ids[0][2]) > 3:
                return {"value": {"disciplinas_ids": disciplinas_ids[0][2][:3]},
                        "warning": {"title": u"Alerta",
                                    "message": u"É permitido selecionar no máximo 3 disciplinas para \"Tutoria\"."}}
#             elif not modalidade:
#                 return {"value": {"disciplinas_ids": []},
#                         "warning": {"title": u"Modalidade",
#                                     "message": u"Modalidade não selecionada"}}
        return {}
    
    def onchange_processo_seletivo(self, cr, uid, ids, context=None):
        return {"value": {"disciplinas_ids": []}}

    def _get_banco(self, cr, inscricao, context=None):
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

    def botao_inscrever(self, cr, uid, ids, context=None):
        inscricao_model = self.pool.get("ud.monitoria.inscricao")
        perfil_model = self.pool.get("ud.perfil")
        pessoa_model = self.pool.get("ud.employee")
        res_id = False
        for inscricao in self.browse(cr, uid, ids, context=context):
            dados_bancarios_id = False
            pessoa_dados = {}
            if inscricao.celular and inscricao.controle in ["c", "ce"]:
                pessoa_dados["mobile_phone"] = inscricao.celular
            if inscricao.email and inscricao.controle in ["e", "ce"]:
                pessoa_dados["work_email"] = inscricao.email
            if pessoa_dados:
                pessoa_id = perfil_model.read(cr, uid, inscricao.perfil_id.id, ["ud_papel_id"], context=context, load="_classic_write")["ud_papel_id"]
                pessoa_model.write(cr, SUPERUSER_ID, pessoa_id, pessoa_dados, context=context)
            if inscricao.banco_id:
                dados_bancarios_id = self._get_banco(cr, inscricao, context)
            pontuacoes = [(0, 0, {"disciplina_id": disc.id,
                                  "pontuacoes_ids": [(0, 0, {"criterio_avaliativo_id": crit.id})
                                                     for crit in inscricao.processo_seletivo_id.criterios_avaliativos_ids]})
                           for disc in inscricao.disciplinas_ids]
            dados = {"perfil_id": inscricao.perfil_id.id,
                     "cpf_nome": inscricao.nome_cpf, "cpf": inscricao.cpf,
                     "identidade_nome": inscricao.nome_identidade, "identidade": inscricao.identidade,
                     "hist_analitico_nome": inscricao.nome_hist_analitico, "hist_analitico": inscricao.hist_analitico,
                     "processo_seletivo_id": inscricao.processo_seletivo_id.id,
                     "modalidade": inscricao.modalidade, "turno": inscricao.turno, "bolsista": inscricao.bolsista,
                     "disciplinas_ids": [(6, 0, [disc.id for disc in inscricao.disciplinas_ids])],
                     "dados_bancarios_id": dados_bancarios_id, "state": "analise",
                     "pontuacoes_ids": pontuacoes}
            res_id = inscricao_model.create(cr, SUPERUSER_ID, dados, context=context)
        obj_model = self.pool.get('ir.model.data')
        form_id = obj_model.get_object_reference(cr, uid, "ud_monitoria", "ud_monitoria_inscricao_form_view")[1]
        return {
            "name": u"Gerenciamento de Inscrições",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "ud.monitoria.inscricao",
            "view_id": form_id,
            # "view_id": False,
            "type": "ir.actions.act_window",
            "nodestroy": True,
            "res_id": res_id or False,
            "target": "current",
        }
