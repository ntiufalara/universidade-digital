# coding: utf8

from openerp.osv import osv, fields

class finalizar_wiz (osv.osv_memory):
    _name = "finalizar.wiz"
    _columns = {
                "finalizar":fields.text("Descrição do serviço executado", required=True),
                }
    def finalizar (self, cr, uid, ids, ctx):
        lt = self.read(cr, uid, ids)[0]
        valores = {'finalizar':lt["finalizar"], "state":"finalizada"}
        self.pool.get("ud.solicitacao").write(cr, uid)