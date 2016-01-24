# encoding: UTF-8
from openerp.osv import osv, fields


class ud_solicitacao(osv.Model):
	_name = 'ud.solicitacao'

	_inherit = 'ud.solicitacao'

	_columns = {
		'pat' : fields.many2one('patrimonio.bem', 'Patrimônio ref.')
	}

	_defaults = {
		'manutencao' : lambda self, cr, uid, context: self.manutencao_default(cr, uid, context),
		'pat': lambda self, cr, uid, context: self.patrimonio_default(cr, uid, context)
	}

	def patrimonio_default(self, cr, uid, context):
		if context.has_key('pat'):
			return context['pat']
		return False

	def manutencao_default(self, cr, uid, context):
		if context.has_key('pat'):
			return 'equip'
		return False