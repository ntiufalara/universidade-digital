# coding: utf-8
'''
Created on 7 de mai de 2016

@author: cloves
'''

from openerp.osv import osv, fields


class AnexoWizard(osv.TransientModel):
    _name = "ud.monitoria.anexo.wizard"
    _description = u"Wizard para anexo de arquivo"
    
    _columns = {
        "_id": fields.integer("ID", invisible=True),
        "name": fields.char(u"Nome"),
        "arquivo": fields.binary(u"Arquivo", filters="*.pdf,*.png,*.jpg,*.jpeg"),
        "anexos_ids": fields.many2one("ud.monitoria.anexos.wizard", invisible=True, ondelete="cascade"),
    }


class AnexosWizard(osv.TransientModel):
    _name = "ud.monitoria.anexos.wizard"
    _description = u"Wizard para criar/remover anexos"
    
    _columns = {
        "anexos_ids": fields.one2many("ud.monitoria.anexo.wizard", "anexos_ids", u"Anexos"),
    }
    
    def default_get(self, cr, uid, fields_list, context=None):
        res = super(AnexosWizard, self).default_get(cr, uid, fields_list, context=context)
        if context.get("active_model", False) and context.get("active_id", False):
            res["anexos_ids"] = []
            for anexo in self.pool.get(context.get("active_model")).browse(cr, uid, context.get("active_id")).anexos_ids:
                res["anexos_ids"].append((0, 0, {"_id": anexo.id, "name": anexo.name, "arquivo": anexo.arquivo, "state":"atual"}))
        return res
    
    def botao_salvar(self, cr, uid, ids, context=None):
        if context.get("active_model", False) and context.get("active_id", False):
            modelo = self.pool.get(context.get("active_model"))
            anexo_model = self.pool.get("ud.monitoria.anexo")
            anexo_wizard_model = self.pool.get("ud.monitoria.anexo.wizard")
            
            antigos_ids = modelo.read(cr, uid, context.get("active_id"), ["anexos_ids"], load="_classic_write")["anexos_ids"]
            manter_ids = []
            novos_ids = []
            for anexos in self.read(cr, uid, ids, ["anexos_ids"], load="_classic_write"):
                for anexo in anexo_wizard_model.read(cr, uid, anexos["anexos_ids"], ["_id", "name", "arquivo"], load="_classic_write"):
                    if anexo["_id"]:
                        manter_ids.append(anexo["_id"])
                    else:
                        novos_ids.append(
                            anexo_model.create(cr, uid, {"name": anexo["name"], "arquivo": anexo["arquivo"]})
                        )
            anexo_model.unlink(cr, uid, list(set(antigos_ids).difference(manter_ids)))
            modelo.write(cr, uid, [context.get("active_id")], {"anexos_ids": [(6, 0, novos_ids+manter_ids)]})
        return True
