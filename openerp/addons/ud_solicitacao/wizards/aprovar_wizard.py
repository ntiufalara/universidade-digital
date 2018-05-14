# coding: utf8

from openerp.osv import osv, fields

class aprovar_wiz (osv.osv_memory):
    _name = "aprovar.wiz"
    _columns = {
                'previsao': fields.date("Previsão para execução ", required=True),
                }
    _defaults = {
                'previsao': fields.date.today(),
                }

    def aprovar (self, cr, uid, ids, ctx):
        lt = self.read(cr, uid, ids)[0]
        valores = {'previsao':lt["previsao"],"state":"aprovada"}
        self.pool.get("ud.solicitacao").write(cr, uid, ctx["active_ids"], valores)