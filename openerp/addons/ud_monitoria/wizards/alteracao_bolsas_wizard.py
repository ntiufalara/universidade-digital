# coding: utf-8

from openerp.osv import osv, fields


class AdicionarBolsaWizard(osv.TransientModel):
    _name = "ud.monitoria.adicionar.bolsa.wizard"
    _description = u"Inclusão de bolsa de monitoria para discente (UD)"
    
    _columns = {
        "curso_id": fields.many2one("ud.curso", u"Curso", required=True, domain="[('is_active', '=', True)]"),
        "disciplina_id": fields.many2one("ud.disciplina", u"Disciplina", required=True, domain="[('id', 'in', [])]"),
        # "bolsistas_ids": fields.many2many("ud.monitoria.discente", "ud_monitoria_bolsista_add_bolsa", "add_bolsa_id", "discente_id", u"Discente", required=True),
    }
    
    def default_get(self, cr, uid, fields_list, context=None):
        res = super(AdicionarBolsaWizard, self).default_get(cr, uid, fields_list, context=context)
        context = context or {}
        if context.get("active_model", False) == "ud.monitoria.documentos.discente" and context.get("active_id", False):
            documento_discente = self.pool.get("ud.monitoria.documentos.discente").browse(cr, uid, context.get("active_id"))
            res["curso_id"] = documento_discente.disciplina_id.curso_id.id
            res["disciplina_id"] = documento_discente.disciplina_id.id
            if documento_discente.disciplina_id.state != "finalizado":
                res["bolsistas_ids"] = [(4, documento_discente.discente_id)]
        return res
    
    def onchange_curso(self, cr, uid, ids, curso_id, context=None):
        res = {"value": {"disciplina_id": False, "bolsistas_ids": []}}
        if curso_id:
            oferta_model = self.pool.get("ud.monitoria.oferta.disciplina")
            ofertas = oferta_model.search(cr, uid, [("curso_id", "=", curso_id)])
            disciplinas_ids = []
            if ofertas:
                for oferta in oferta_model.read(cr, uid, ofertas, ["disciplina_id"], load="_classic_write"):
                    disciplinas_ids.append(oferta["disciplina_id"])
            res["domain"] = {"disciplina_id": [('ud_disc_id', '=', curso_id),('id', 'in', disciplinas_ids)],
                             "bolsistas_ids": [("id", "in", [])]}
        return res
    
    def onchange_disciplina(self, cr, uid, ids, disciplina_ids, context=None):
        res = {"value": {"bolsistas_ids": []}}
        if disciplina_ids:
            pass
        
        return res
