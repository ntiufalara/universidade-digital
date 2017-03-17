# coding: utf-8
from openerp.osv import osv, fields


class RelatorioWizard(osv.TransientModel):
    _name = "ud.monitoria.relatorio.wizard"
    _description = u"Anexo de parecer de relatório (UD)"

    _columns = {
        "relatorio_id": fields.many2one("ud.monitoria.relatorio", u"Relatório", ondelete="cascade", required=True),
        "parecer_nome": fields.char(u"Nome Parecer", help=u"Parecer do Professor Orientador"),
        "parecer": fields.binary(u"Parecer", required=True, help=u"Parecer do Professor Orientador"),
        "info": fields.text(u"Informações", help=u"Informações Adicionais"),
    }

    def default_get(self, cr, uid, fields_list, context=None):
        res = super(RelatorioWizard, self).default_get(cr, uid, fields_list, context)
        context = context or {}
        if context.get("active_id", False) and context.get("active_model", False) == "ud.monitoria.relatorio":
            relatorio = self.pool.get("ud.monitoria.relatorio").browse(cr, uid, context["active_id"], context)
            if relatorio.state != "analise":
                raise osv.except_osv(u"Acesso Negado", u"Você não pode alterar registros que não estejam em análise.")
            usuario = relatorio.documentos_id.disciplina_id.orientador_id.user_id
            if not usuario:
                raise osv.except_osv(u"Registro Inexistente", u"Você não possui registro em Pessoa no Núcleo.")
            if usuario.id != uid:
                raise osv.except_osv(u"Acesso Negado", u"Somente o orientador responsável pode realizar essa operação.")
            # if relatorio.parecer:
            #     raise osv.except_osv(u"Parecer anexado", u"Já existe um arquivo no campo parecer.")
            res["relatorio_id"] = relatorio.id
            res["parecer_nome"] = relatorio.parecer_nome
            res["parecer"] = relatorio.parecer
            res["info"] = relatorio.info
        else:
            raise osv.except_osv(u"Acesso Indisponível",
                                 u"O acesso dessa interface deve ser feita a partir de um relatório de discente.")
        return res

    def salvar(self, cr, uid, ids, context=None):
        for rel in self.browse(cr, uid, ids, context):
            rel.relatorio_id.write({"parecer_nome": rel.parecer_nome, "parecer": rel.parecer, "info": rel.info})
        return True
