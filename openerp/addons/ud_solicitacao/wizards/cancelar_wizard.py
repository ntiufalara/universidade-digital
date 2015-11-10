# coding: utf8

from openerp.osv import fields, osv

class cancelar_wiz (osv.osv_memory):
    _name = "cancelar_wiz"
    _columns = {
                "motivo": fields.text("Motivo", required=True),
                "data_cancel": fields.date("Cancelado em:", required=True),
                }
    _defaults = {
                 'data_cancel': fields.date.today(),
                 }
    
    def cancelar (self, cr, uid, ids, ctx):
        lt = self.read(cr, uid, ids)[0]
        valores = {'motivo':lt["motivo"],"data_cancelamento":lt["data_cancel"], "state":"cancelada"}
        self.pool.get("ud.solicitacao").write(cr, uid, ctx["active_ids"], valores)