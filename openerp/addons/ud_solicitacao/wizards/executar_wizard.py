# coding: utf8

from openerp.osv import fields, osv

class executar_wiz (osv.osv_memory):
    _name = "executar.wiz"
    _columns = {
                "execucao":fields.text("Descrição do Serviço", required=True),
                "data_execucao": fields.date("Data da execução", required=True),
                }
    _defualts = {
                 "data_execucao": fields.date.today(),
                 }
    def execucao (self, cr, uid, ids, ctx):
        lt = self.read(cr, uid, ids)[0]
        valores = {'execucao':lt["execucao"], "data_execucao":lt["data_execucao"],"state":"execucao"}
        self.pool.get("ud.solicitacao").write(cr, uid)