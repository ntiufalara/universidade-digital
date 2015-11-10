#encoding: utf-8
from openerp.osv import fields, osv


class nova_solicitacao(osv.TransientModel):
    
    _name = "nova.solicitacao.patrimonio"
    _description = "Cria uma nova solicitacao a partir de um bem"
    _columns = {
        'solicitacao_id': fields.one2many('ud.solicitacao', 'pat', string=u"Solicitações")
        
    }