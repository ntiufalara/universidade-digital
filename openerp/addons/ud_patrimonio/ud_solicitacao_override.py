# encoding: UTF-8
from openerp.osv import osv, fields


class ud_solicitacao(osv.Model):
    _name = 'ud.solicitacao'

    _inherit = 'ud.solicitacao'

    _columns = {
        'pat': fields.many2one('patrimonio.bem', 'Patrimônio ref.')
    }

    _defaults = {
        'manutencao': lambda self, cr, uid, context: self.manutencao_default(cr, uid, context),
        'pat': lambda self, cr, uid, context: self.patrimonio_default(cr, uid, context),
        'local_camp': lambda self, cr, uid, context: self.campus_default(cr, uid, context),
        'local_polo': lambda self, cr, uid, context: self.polo_default(cr, uid, context),
        'local_espaco': lambda self, cr, uid, context: self.espaco_default(cr, uid, context),

    }

    def patrimonio_default(self, cr, uid, context):
        if context.has_key('pat'):
            return context['pat']
        return False

    def manutencao_default(self, cr, uid, context):
        if context.has_key('pat'):
            return 'equip'
        return False

    def campus_default(self, cr, uid, context):
        if context.has_key('espaco'):
            espaco = self.pool.get('ud.espaco').browse(cr, uid, context.get('espaco'))
            return espaco.local_polo.campus_id.id
        return False

    def polo_default(self, cr, uid, context):
        if context.has_key('espaco'):
            espaco = self.pool.get('ud.espaco').browse(cr, uid, context.get('espaco'))
            return espaco.local_polo.id
        return False

    def espaco_default(self, cr, uid, context):
        if context.has_key('espaco'):
            espaco = self.pool.get('ud.espaco').browse(cr, uid, context.get('espaco'))
            return espaco.id
        return False