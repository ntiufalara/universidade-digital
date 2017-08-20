# coding: utf-8
from openerp import SUPERUSER_ID
from openerp.osv import osv, fields


class AlterarOrientadorWizard(osv.TransientModel):
    _name = "ud.monitoria.alterar.orientador.wizard"
    _description = u"Alteração de orientador de disciplinas ativas"

    def disciplina_ativa(self, cr, uid, ids, context):
        """
        Validador para verificar se a disciplina que se deseja fazer a mudança de orientador está ativa.

        :return: Boolean
        """
        for alt in self.browse(cr, uid, ids, context):
            if not alt.disciplina_id.is_active:
                return False
        return True

    _columns = {
        "disciplina_id": fields.many2one("ud.monitoria.disciplina", u"Disciplina", required=True,
                                         domain=[("is_active", "=", True)]),
        "perfil_id": fields.many2one("ud.perfil", u"SIAPE", required=True, domain=[("tipo", "=", "p")]),
        "orientador_id": fields.related("perfil_id", "ud_papel_id", type="many2one", relation="ud.employee",
                                        string=u"Orientador", readonly=True),
    }

    _constraints = [
        (disciplina_ativa, u"Não é permitido alterar orientador de disciplinas inativas", [u"Disciplina"])
    ]

    def default_get(self, cr, uid, fields_list, context=None):
        """
        === Extensão do método osv.TransientModel.default_get
        Caso o modelo a
        """
        res = super(AlterarOrientadorWizard, self).default_get(cr, uid, fields_list, context)
        if context.get("active_id", False) and context.get("active_model", False) == "ud.monitoria.disciplina":
            res["disciplina_id"] = context["active_id"]
        return res

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        """
        === Extensão do método osv.TransientModel.fields_view_get
        Para atender a necessidade na view, foi adicionado a opção de filtro de perfis
        caso o ID da disciplina tenha sido informado. Isso permitirá que a modificação seja realizada apenas para
        professores do mesmo curso.
        """
        context = context or {}
        res = super(AlterarOrientadorWizard, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
        if "perfil_id" in res["fields"]:
            domain_temp = res["fields"]["perfil_id"].get("domain", [])
            if isinstance(domain_temp, str):
                domain_temp = list(eval(domain_temp))
            if context.get("disciplina_id", False):
                domain = []
                for d in domain_temp:
                    if d[0] not in ["id", "ud_cursos"]:
                        domain.append(d)
                del domain_temp
                disciplina = self.pool.get("ud.monitoria.disciplina").browse(cr, SUPERUSER_ID, context["disciplina_id"])
                domain += [("id", "!=", disciplina.perfil_id.id), ('ud_cursos', '=', disciplina.curso_id.id)]
                res["fields"]["perfil_id"]["domain"] = domain
        return res

    def onchange_perfil(self, cr, uid, ids, perfil_id, context=None):
        """
        Método usado para atualizar os dados do campo "orientador_id" caso "perfil_id" seja modificado.
        """
        if perfil_id:
            perfil_id = self.pool.get("ud.perfil").browse(cr, uid, perfil_id, context)
            return {"value": {"orientador_id": perfil_id.ud_papel_id.id}}
        return {"value": {"orientador_id": False}}

    def botao_alterar(self, cr, uid, ids, context=None):
        """
        Muda o orientador de uma disciplina para outra

        :param cr: Cursor
        :param uid: ID do usuário logado
        :param ids: Lista de ids do modelo atual
        :return: True

        :raise osv.except_osv: Se usuário logado não tiver ou possuir múltiplos vínculos com Perfil do núcleo.
        """
        doc_orientador_model = self.pool.get("ud.monitoria.documentos.orientador")
        pessoa_model = self.pool.get("ud.employee")
        for alt in self.browse(cr, uid, ids, context):
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
            doc_orientador_antigo = doc_orientador_model.search(cr, uid, [("disciplina_id", "=", alt.disciplina_id.id),
                                                                          ("is_active", "=", True)])
            doc_orientador_antigo = doc_orientador_model.browse(cr, uid, doc_orientador_antigo[0] if doc_orientador_antigo else None)
            doc_orientador_antigo.write({"is_active": False})
            alt.disciplina_id.write({"perfil_id": alt.perfil_id.id})
            doc_orientador = doc_orientador_model.search(cr, uid, [("disciplina_id", "=", alt.disciplina_id.id), ("is_active", "=", False)])
            if doc_orientador:
                doc_orientador_model.browse(cr, uid, doc_orientador[0]).write({"is_active": True})
            else:
                doc_orientador_model.create(cr, SUPERUSER_ID, {"disciplina_id": alt.disciplina_id.id, "perfil_id": alt.perfil_id.id})
            evento = {
                "responsavel_id": responsavel[0],
                "name": u'Orientador da disciplina de "%s" alterado' % alt.disciplina_id.disciplina_id.name,
                "envolvidos_ids": [(6, 0, [doc_orientador_antigo.orientador_id.id, alt.perfil_id.ud_papel_id.id])],
                "descricao": u'O orientador da disciplina de "%s" foi modificado de "%s" (SIAPE: %s) para "%s" (SIAPE: %s)' % (
                    alt.disciplina_id.disciplina_id.name,
                    doc_orientador_antigo.orientador_id.name,
                    doc_orientador_antigo.perfil_id.matricula,
                    alt.perfil_id.ud_papel_id.name,
                    alt.perfil_id.matricula,
                ),
            }
            alt.disciplina_id.semestre_id.write({"eventos_ids": [(0, 0, evento)]})
        return True
