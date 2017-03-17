# encoding: UTF-8
from openerp.osv import osv, fields


class ud_solicitacao(osv.Model):
    _name = 'ud.solicitacao'
    _inherit = 'ud.solicitacao'

    _gera_pdf = lambda self, cr, uid, ids, field, args, context: self.gera_pdf(cr, uid, ids, field, args, context)

    _columns = {
        u'pat': fields.many2one('patrimonio.bem', 'Patrimônio ref.'),
        # u'pdf_os': fields.function(_gera_pdf, string=u"PDF Ordem de serviço", type="binary"),
    }

    _defaults = {
        u'manutencao': lambda self, cr, uid, context: self.manutencao_default(cr, uid, context),
        u'pat': lambda self, cr, uid, context: self.patrimonio_default(cr, uid, context),
        u'local_camp': lambda self, cr, uid, context: self.campus_default(cr, uid, context),
        u'local_polo': lambda self, cr, uid, context: self.polo_default(cr, uid, context),
        u'local_espaco': lambda self, cr, uid, context: self.espaco_default(cr, uid, context),
    }

    # def gera_pdf(self, cr, uid, ids, field, args, context):
    #     this = self.browse(cr, uid, ids)
    #     # template = open('template_documentos/etiqueta.html', 'r').read()
    #     template = open(os.path.join(os.path.dirname(__file__), "template_documentos", 'etiqueta.html'), 'r').read()
    #     pdf = Pdf(template, {}).pdf
    #     print pdf

    def patrimonio_default(self, cr, uid, context):
        if context.get('pat'):
            return context['pat']
        return False

    def manutencao_default(self, cr, uid, context):
        if context.get('pat'):
            return 'equip'
        return False

    def campus_default(self, cr, uid, context):
        if context.get('espaco'):
            espaco = self.pool.get('ud.espaco').browse(cr, uid, context.get('espaco'))
            return espaco.local_polo.campus_id.id
        return False

    def polo_default(self, cr, uid, context):
        if context.get('espaco'):
            espaco = self.pool.get('ud.espaco').browse(cr, uid, context.get('espaco'))
            return espaco.local_polo.id
        return False

    def espaco_default(self, cr, uid, context):
        if context.get('espaco'):
            espaco = self.pool.get('ud.espaco').browse(cr, uid, context.get('espaco'))
            return espaco.id
        return False
