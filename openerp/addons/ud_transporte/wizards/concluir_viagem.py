# -*- encoding: UTF-8 -*-
from openerp.osv import osv, fields

class concluir_viagem (osv.osv_memory):
    _name = 'ud.transporte.concluir.viagem'
    _columns = {
                'ocorrencia':fields.text('Ocorrências'),
                'notas': fields.text('Notas'),
                'km_inicial':fields.float('Km Inicial'),
                'km_final':fields.float('Km final'),
                'custo':fields.float('Custo',help="Deixe em branco (0), caso seja sem custeio"),
                'abastecimento':fields.float('Abastecimento'),
                'preco_combustivel':fields.float('Preço do combustível'),
                'km_rodado':fields.integer('Km rodado', readonly=True),
                }
    
    def onchange_km(self, cr, uid, ids, km_inicial, km_final, contexto=None):
        res = {}
        if (km_final < km_inicial):
            km_final = km_inicial
            res['km_final'] = km_final
        result = km_final - km_inicial
        res['km_rodado'] = result        
        return {'value':res}
    def salvar(self, cr, uid, ids, ctx=None):
        lt = self.read(cr, uid, ids)[0]
        valores = {'ocorrencia':lt["ocorrencia"],"state":"concluida", 'notas':lt['notas'], 'km_rodado':lt['km_rodado'], 'preco_combustivel':lt['preco_combustivel'], 'abastecimento':lt['abastecimento'], 'custo':lt['custo'], 'km_inicial':lt['km_inicial'], 'km_final':lt['km_final']}
        self.pool.get("ud.transporte.viagem").write(cr, uid)