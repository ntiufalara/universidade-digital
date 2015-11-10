# coding: utf8
from osv import fields, osv

class cancelar(osv.osv_memory):
    _name = "cancelar"
    _columns = {
                "motivo": fields.text("Motivo", required=True),
                "data_cancelamento": fields.date("Cancelado em:", required=True),
                }
    _defaults = {
                 'data_cancelamento': fields.date.today(),
                 }
    
    def cancelar (self, cr, uid, ids, ctx):
        lt = self.read(cr, uid, ids)[0]
        valores = {'motivo':lt["motivo"],"data_cancelamento":lt["data_cancelamento"], "state":"cancelada"}
        self.pool.get("ud.reserva").write(cr, uid, ctx["active_ids"], valores)
