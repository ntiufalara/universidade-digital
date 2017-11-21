# coding: utf-8
from openerp import SUPERUSER_ID
from openerp.osv import osv, fields
from openerp.addons.ud.ud import _TIPOS_BOLSA

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
        raise osv.except_osv(u"Dados Bancários duplicados", u"Não é permitido duplicar dados bancários!")
    dados = {"banco_id": browse_record.banco_id.id, "ud_conta_id": usuario_id, "agencia": browse_record.agencia,
             "dv_agencia": browse_record.dv_agencia, "conta": browse_record.conta, "dv_conta": browse_record.dv_conta,
             "operacao": browse_record.operacao}
    return dados_bancarios_model.create(cr, SUPERUSER_ID, dados, context=context)


class AdicionarBolsaWizard(osv.TransientModel):
    _name = "ud.monitoria.bolsa.adicionar.wizard"
    _description = u"Inclusão de bolsa de monitoria para discente (UD)"

    _STATES = [
        ("n_bolsista", u"Não Bolsista"),
        ("reserva", u"Cadastro de Reserva"),
    ]

    _columns = {
        "semestre_id": fields.many2one("ud.monitoria.registro", u"Semestre", required=True, readonly=True),
        "curso_id": fields.many2one("ud.curso", u"Curso", required=True, domain="[('is_active', '=', True)]"),
        "disciplina_id": fields.many2one("ud.monitoria.disciplina", u"Disciplinas", required=True,
                                         domain="[('semestre_id', '=', semestre_id), ('curso_id', '=', curso_id), "
                                                "('is_active', '=', True)]"),
        "bolsas": fields.related("disciplina_id", "bolsas", type="integer", string=u"Bolsas disponíveis",
                                  help=u"Número de bolsas disponíveis para a disciplina"),
        "valor_bolsa": fields.float(u"Bolsa (R$)"),
        "tutor": fields.boolean(u"Tutor?"),
        "status": fields.selection(_STATES, u"Status", required=True),
        "doc_discente_id": fields.many2one("ud.monitoria.documentos.discente", u"Discente", required=True,
                                             domain="[('disciplina_id', '=', disciplina_id), ('tutor', '=', tutor), "
                                                    "('is_active', '=', True), ('state', '=', status)]"),
        # DADOS BANCÁRIOS
        "dados_bancarios_id": fields.many2one("ud.dados.bancarios", u"Dados Bancários", domain=[('id', '=', False)]),
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
        res = super(AdicionarBolsaWizard, self).default_get(cr, uid, fields_list, context)
        res["status"] = "n_bolsista"
        res["valor_bolsa"] = 400.
        context = context or {}
        if context.get("active_id", False):
            if context.get("active_model", False) == "ud.monitoria.registro":
                res["semestre_id"] = context.get("active_id")
            elif context.get("active_model", False) == "ud.monitoria.documentos.discente":
                doc = self.pool.get("ud.monitoria.documentos.discente").browse(cr, uid, context.get("active_id"), context)
                if doc.state == "bolsista":
                    raise osv.except_osv(u"Discente bolsista", u"O discente já é bolsista")
                elif not doc.is_active and doc.state != "reserva":
                    raise osv.except_osv(u"Documento do discente inativo",
                                         u"Não é possível alterar o status de discentes inativos")
                res["semestre_id"] = doc.disciplina_id.semestre_id.id
                res["curso_id"] = doc.disciplina_id.curso_id.id
                res["disciplina_id"] = doc.disciplina_id.id
                res["tutor"] = doc.tutor
                res["status"] = doc.state
                res["doc_discente_id"] = doc.id
        return res

    def onchange_curso(self, cr, uid, ids, semestre_id, curso_id, disciplina_id, context=None):
        if not (semestre_id and curso_id):
            return {"value": {"disciplina_id": False}}
        args = [("id", "=", disciplina_id), ("curso_id", "=", curso_id), ("semestre_id", "=", semestre_id)]
        disc = self.pool.get("ud.monitoria.disciplina").search(cr, uid, args, context=context)
        if not disc:
            return {"value": {"disciplina_id": False}}
        return {}

    def onchange_disciplina(self,  cr, uid, ids, disciplina_id, doc_discente_id, context=None):
        if disciplina_id:
            disciplina = self.pool.get("ud.monitoria.disciplina").browse(cr, uid, disciplina_id, context)
            valores = {"bolsas": disciplina.bolsas_disponiveis()}
            if doc_discente_id:
                doc_discente = self.pool.get("ud.monitoria.documentos.discente").browse(cr, uid, doc_discente_id, context)
                if doc_discente.disciplina_id.id == disciplina_id:
                    valores["doc_discente_id"] = doc_discente_id
                else:
                    valores["doc_discente_id"] = False
            return {"value": valores}
        return {"value": {"doc_discente_id": False, "bolsas": 0}}

    def onchange_doc_discente(self, cr, uid, ids, doc_discente_id, dados_bancarios_id, context=None):
        if doc_discente_id:
            doc = self.pool.get("ud.monitoria.documentos.discente").browse(cr, uid, doc_discente_id, context)
            if not dados_bancarios_id:
                dados_bancarios_id = getattr(doc.dados_bancarios_id, "id", False)
            return {"value": {"dados_bancarios_id": dados_bancarios_id},
                    "domain": {"dados_bancarios_id": [("ud_conta_id", "=", doc.discente_id.id)]}}
        return {"value": {"dados_bancarios_id": False},
                "domain": {"dados_bancarios_id": [("id", "=", False)]}}

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

    def botao_adicionar(self, cr, uid, ids, context=None):
        perfil_model = self.pool.get("ud.perfil")
        for add in self.browse(cr, uid, ids, context):
            if add.bolsas == 0:
                raise osv.except_osv(u"Bolsas Insuficientes", u"Não há bolsas disponíveis para essa disciplina")
            elif not add.doc_discente_id.is_active and add.doc_discente_id.state != "reserva":
                raise osv.except_osv(u"Documento do discente inativo",
                                     u"O discente não pode ser classificado como bolsista")
            matricula = add.doc_discente_id.discente_id.matricula
            for perfil in add.doc_discente_id.discente_id.papel_ids:
                if perfil.matricula == matricula and perfil.tipo == "a":
                    if perfil.is_bolsista:
                        raise osv.except_osv(
                            u"Discente bolsista",
                            u"O discente \"{}\" sob matrícula \"{}\" possui bolsa do tipo: \"{}\"".format(
                                add.doc_discente_id.discente_id.name, matricula, TIPOS_BOLSA[perfil.tipo_bolsa]
                            )
                        )
                    break
            if not perfil:
                raise osv.except_osv(
                    u"Perfil excluído",
                    u"O perfil do discente para a matrícula \"%s\" não existe ou foi excluído" % matricula or ""
                )
            responsavel = self.pool.get("ud.employee").search(cr, SUPERUSER_ID, [("user_id", "=", uid)], limit=2)
            if not responsavel:
                raise osv.except_osv(
                    u"Registro Inexistente",
                    u"Não é possível realizar essa alteração enquanto seu login não estiver vinculado ao núcleo"
                )
            if len(responsavel) > 1:
                raise osv.except_osv(
                    u"Multiplos vínculos",
                    u"Não é possível realizar essa alteração enquanto seu login possuir multiplos vínculos no núcleo"
                )
            perfil_model.write(cr, SUPERUSER_ID, perfil.id, {
                "is_bolsista": True, "tipo_bolsa": "m", "valor_bolsa": ("%.2f" % add.valor_bolsa).replace(".", ",")
            })
            dados_bancarios = add.dados_bancarios_id.id
            if not dados_bancarios:
                dados_bancarios = get_banco(self, cr, add, add.doc_discente_id.discente_id.id, context)
            dados = {"state": "bolsista", "is_active": True}
            if dados_bancarios:
                dados["dados_bancarios_id"] = dados_bancarios
            add.doc_discente_id.write(dados)
            evento = {
                "responsavel_id": responsavel[0],
                "name": u"Adição de bolsa: \"%s\"" % add.doc_discente_id.discente_id.name,
                "envolvidos_ids": [(4, add.doc_discente_id.discente_id.id)],
                "descricao": u"Uma bolsa de R$ %s foi vinculada para o(a) discente \"%s\" sob matrícula \"%s\"." % (
                    ("%.2f" % add.valor_bolsa).replace(".", ","),
                    add.doc_discente_id.discente_id.name.upper(), matricula
                )
            }
            add.semestre_id.write({"eventos_ids": [(0, 0, evento)]})
        return True


class TransferirBolsaWizard(osv.TransientModel):
    _name = "ud.monitoria.bolsa.transferir.wizard"
    _description = u"Transferência de bolsa de monitoria (UD)"

    _STATES = [
        ("n_bolsista", u"Não Bolsista"),
        ("reserva", u"Cadastro de Reserva"),
    ]

    _columns = {
        "semestre_id": fields.many2one("ud.monitoria.registro", u"Semestre", required=True, readonly=True),

        "curso_id_de": fields.many2one("ud.curso", u"Curso", required=True, domain="[('is_active', '=', True)]"),
        "disciplina_id_de": fields.many2one("ud.monitoria.disciplina", u"Disciplinas", required=True,
                                         domain="[('semestre_id', '=', semestre_id), ('curso_id', '=', curso_id_de), "
                                                "('is_active', '=', True)]"),
        "tutor_de": fields.boolean(u"Tutor?"),
        "doc_discente_id_de": fields.many2one("ud.monitoria.documentos.discente", u"Discente", required=True,
                                              domain="[('is_active', '=', True), ('state', '=', 'bolsista'), "
                                                     "('disciplina_id', '=', disciplina_id_de), ('tutor', '=', tutor_de)]"),

        "curso_id_para": fields.many2one("ud.curso", u"Curso", required=True, domain="[('is_active', '=', True)]"),
        "disciplina_id_para": fields.many2one("ud.monitoria.disciplina", u"Disciplinas", required=True,
                                         domain="[('semestre_id', '=', semestre_id), ('curso_id', '=', curso_id_para), "
                                                "('is_active', '=', True)]"),
        "tutor_para": fields.boolean(u"Tutor?"),
        "status_para": fields.selection(_STATES, u"Status", required=True),
        "doc_discente_id_para": fields.many2one("ud.monitoria.documentos.discente", u"Discente", required=True,
                                                domain="[('is_active', '=', True), ('state', '=', status_para), "
                                                       "('disciplina_id', '=', disciplina_id_para), "
                                                       "('tutor', '=', tutor_para)]"),
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
        res = super(TransferirBolsaWizard, self).default_get(cr, uid, fields_list, context)
        context = context or {}
        if context.get("active_id", False):
            if context.get("active_model", False) == "ud.monitoria.registro":
                res["semestre_id"] = context.get("active_id")
            elif context.get("active_model", False) == "ud.monitoria.documentos.discente":
                doc = self.pool.get("ud.monitoria.documentos.discente").browse(cr, uid, context.get("active_id"),
                                                                               context)
                if doc.state != "bolsista":
                    raise osv.except_osv(u"Discente bolsista", u"O discente já é bolsista")
                elif not doc.is_active:
                    raise osv.except_osv(u"Documento do discente inativo",
                                         u"O discente não pode ser classificado como bolsista")
                res["semestre_id"] = doc.disciplina_id.semestre_id.id
                res["curso_id_de"] = doc.disciplina_id.curso_id.id
                res["disciplina_id_de"] = doc.disciplina_id.id
                res["tutor_de"] = doc.tutor
                res["status_de"] = doc.state
                res["doc_discente_id_de"] = doc.id
        return res

    def onchange_curso(self, cr, uid, ids, comp, semestre_id, curso_id, disciplina_id, context=None):
        if not (semestre_id and curso_id):
            return {"value": {"disciplina_id_" + comp: False}}
        args = [("id", "=", disciplina_id), ("curso_id", "=", curso_id), ("semestre_id", "=", semestre_id)]
        disc = self.pool.get("ud.monitoria.disciplina").search(cr, uid, args, context=context)
        if not disc:
            return {"value": {"disciplina_id_" + comp: False}}
        return {}

    def onchange_disciplina(self,  cr, uid, ids, comp, disciplina_id, doc_discente_id, context=None):
        if disciplina_id and doc_discente_id:
            doc_discente = self.pool.get("ud.monitoria.documentos.discente").browse(cr, uid, doc_discente_id, context)
            doc_discente_id = doc_discente_id if doc_discente.disciplina_id.id == disciplina_id else False
            return {
                "value": {"doc_discente_id_" + comp: doc_discente_id}
            }
        return {"value": {"doc_discente_id_" + comp: False}}

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

    def botao_transferir(self, cr, uid, ids, context=None):
        perfil_model = self.pool.get("ud.perfil")
        for transf in self.browse(cr, uid, ids, context):
            matricula = transf.doc_discente_id_para.discente_id.matricula
            for perfil in transf.doc_discente_id_para.discente_id.papel_ids:
                if perfil.matricula == matricula and perfil.tipo == "a":
                    if perfil.is_bolsista:
                        raise osv.except_osv(
                            u"Discente bolsista",
                            u"O discente \"{}\" sob matrícula \"{}\" possui bolsa do tipo: \"{}\"".format(
                                transf.doc_discente_id_para.discente_id.name, matricula,
                                TIPOS_BOLSA[perfil.tipo_bolsa]
                            )
                        )
                    break
            if not perfil:
                raise osv.except_osv(
                    u"Perfil excluído",
                    u"O perfil do discente para a matrícula \"%s\" não existe ou foi excluído" % matricula or ""
                )
            matricula = transf.doc_discente_id_de.discente_id.matricula
            for perfil_de in transf.doc_discente_id_de.discente_id.papel_ids:
                if perfil.matricula == matricula and perfil.tipo == "a":
                    break
            responsavel = self.pool.get("ud.employee").search(cr, SUPERUSER_ID, [("user_id", "=", uid)], limit=2)
            if not responsavel:
                raise osv.except_osv(
                    u"Registro Inexistente",
                    u"Não é possível realizar essa alteração enquanto seu login não estiver vinculado ao núcleo"
                )
            if len(responsavel) > 1:
                raise osv.except_osv(
                    u"Multiplos vínculos",
                    u"Não é possível realizar essa alteração enquanto seu login possuir multiplos vínculos no núcleo"
                )
            valor = perfil_de.valor_bolsa
            perfil_model.write(cr, SUPERUSER_ID, perfil.id, {
                "is_bolsista": True, "tipo_bolsa": "m", "valor_bolsa": valor
            })
            perfil_model.write(cr, SUPERUSER_ID, perfil_de.id, {
                "is_bolsista": False, "tipo_bolsa": False, "valor_bolsa": False
            })
            transf.doc_discente_id_de.write({"state": "n_bolsista"})
            transf.doc_discente_id_para.write({"state": "bolsista", "is_active": True})
            get_banco(self, cr, transf, transf.doc_discente_id_para.discente_id.id, context)
            evento = {
                "responsavel_id": responsavel[0],
                "name": u"Transferência de bolsa",
                "envolvidos_ids": [(4, transf.doc_discente_id_de.discente_id.id),
                                   (4, transf.doc_discente_id_para.discente_id.id)],
                "descricao": u"Transferência de bolsa no valor de R$ %(valor)s do discente %(discente_de)s sob matrícula "
                             u"%(matricula_de)s para o(a) discente \"%(discente_para)s\" sob matrícula"
                             u"\"%(matricula_para)s\"." % {
                    "valor": valor, "discente_de": transf.doc_discente_id_de.discente_id.name.upper(),
                    "matricula_de": perfil_de.matricula,
                    "discente_para": transf.doc_discente_id_de.discente_id.name.upper(),
                    "matricula_para": perfil_de.matricula
                }
            }
            transf.semestre_id.write({"eventos_ids": [(0, 0, evento)]})
        return True


class RemoverBolsaWizard(osv.TransientModel):
    _name = "ud.monitoria.bolsa.remover.wizard"
    _description = u"Remoção de bolsa de discente"

    _columns = {
        "semestre_id": fields.many2one("ud.monitoria.registro", u"Semestre", required=True, readonly=True),
        "curso_id": fields.many2one("ud.curso", u"Curso", required=True, domain="[('is_active', '=', True)]"),
        "disciplina_id": fields.many2one("ud.monitoria.disciplina", u"Disciplinas", required=True,
                                         domain="[('semestre_id', '=', semestre_id), ('curso_id', '=', curso_id), "
                                                "('is_active', '=', True)]"),
        "tutor": fields.boolean(u"Tutor?"),
        "doc_discente_id": fields.many2one("ud.monitoria.documentos.discente", u"Discente", required=True,
                                             domain="[('disciplina_id', '=', disciplina_id), ('tutor', '=', tutor), "
                                                    "('is_active', '=', True), ('state', '=', 'bolsista')]"),
    }

    def default_get(self, cr, uid, fields_list, context=None):
        res = super(RemoverBolsaWizard, self).default_get(cr, uid, fields_list, context)
        context = context or {}
        if context.get("active_id", False):
            if context.get("active_model", False) == "ud.monitoria.registro":
                res["semestre_id"] = context.get("active_id")
            elif context.get("active_model", False) == "ud.monitoria.documentos.discente":
                doc = self.pool.get("ud.monitoria.documentos.discente").browse(cr, uid, context.get("active_id"), context)
                if doc.state != "bolsista":
                    raise osv.except_osv(u"Discente não bolsista", u"O discente não é bolsista")
                elif not doc.is_active:
                    raise osv.except_osv(u"Documento do discente inativo",
                                         u"Não é possível alterar o status de discentes inativos")
                res["semestre_id"] = doc.disciplina_id.semestre_id.id
                res["curso_id"] = doc.disciplina_id.curso_id.id
                res["disciplina_id"] = doc.disciplina_id.id
                res["tutor"] = doc.tutor
                res["doc_discente_id"] = doc.id
        return res

    def onchange_curso(self, cr, uid, ids, semestre_id, curso_id, disciplina_id, context=None):
        if not (semestre_id and curso_id):
            return {"value": {"disciplina_id": False}}
        args = [("id", "=", disciplina_id), ("curso_id", "=", curso_id), ("semestre_id", "=", semestre_id)]
        disc = self.pool.get("ud.monitoria.disciplina").search(cr, uid, args, context=context)
        if not disc:
            return {"value": {"disciplina_id": False}}
        return {}

    def onchange_disciplina(self,  cr, uid, ids, disciplina_id, doc_discente_id, context=None):
        if disciplina_id and doc_discente_id:
            doc_discente = self.pool.get("ud.monitoria.documentos.discente").browse(cr, uid, doc_discente_id, context)
            doc_discente_id = doc_discente_id if doc_discente.disciplina_id.id == disciplina_id else False
            return {
                "value": {"doc_discente_id": doc_discente_id}
            }
        return {"value": {"doc_discente_id": False}}

    def botao_remover(self, cr, uid, ids, context=None):
        perfil_model = self.pool.get("ud.perfil")
        pessoa_model = self.pool.get("ud.employee")
        for rem in self.browse(cr, uid, ids, context):
            matricula = rem.doc_discente_id.discente_id.matricula
            for perfil in rem.doc_discente_id.discente_id.papel_ids:
                if perfil.matricula == matricula and perfil.tipo == "a":
                    if perfil.is_bolsista and perfil.tipo_bolsa != "m":
                        raise osv.except_osv(
                            u"Categoria de bolsa",
                            u"A categoria de bolsa do discente \"{}\" sob matrícula \"{}\" não é pertencente à "
                            u"monitoria: \"{}\"".format(
                                rem.doc_discente_id.discente_id.name, matricula, TIPOS_BOLSA[perfil.tipo_bolsa]
                            )
                        )
                    break
            if not perfil:
                raise osv.except_osv(
                    u"Perfil excluído",
                    u"O perfil do discente para a matrícula \"%s\" não existe ou foi excluído" % matricula or ""
                )
            responsavel = pessoa_model.search(cr, SUPERUSER_ID, [("user_id", "=", uid)], limit=2)
            if not responsavel:
                raise osv.except_osv(
                    u"Registro Inexistente",
                    u"Não é possível realizar essa alteração enquanto seu login não estiver vinculado ao núcleo"
                )
            if len(responsavel) > 1:
                raise osv.except_osv(
                    u"Multiplos vínculos",
                    u"Não é possível realizar essa alteração enquanto seu login possuir multiplos vínculos no núcleo"
                )
            perfil_model.write(cr, SUPERUSER_ID, perfil.id, {
                "is_bolsista": False, "tipo_bolsa": False, "valor_bolsa": False
            })
            rem.doc_discente_id.write({"state": "n_bolsista"})
            evento = {
                "responsavel_id": responsavel[0],
                "name": u"Remoção de bolsa: \"%s\"" % rem.doc_discente_id.discente_id.name,
                "envolvidos_ids": [(4, rem.doc_discente_id.discente_id.id)],
                "descricao": u"A bolsa do discente \"%s\" sob matrícula \"%s\" foi removida." % (
                    rem.doc_discente_id.discente_id.name.upper(), matricula
                )
            }
            rem.semestre_id.write({"eventos_ids": [(0, 0, evento)]})
        return True
