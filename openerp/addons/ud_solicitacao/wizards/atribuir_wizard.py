# coding: utf8

from openerp.osv import osv, fields

class atribuir_wiz (osv.osv_memory):
    _name = "atribuir.wiz"
    _columns = {
                'responsavel': fields.many2one("ud.solicitacao.responsavel", "Responsável: ", required=True),
                }

    def atribuir (self, cr, uid, ids, ctx):
        lt = self.read(cr, uid, ids)[0]
        valores = {'responsavel':lt["responsavel"][0],"state":"atribuida"}
        self.pool.get("ud.solicitacao").write(cr, uid, ctx["active_ids"], valores)