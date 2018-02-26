# encoding: UTF-8

from openerp.osv import osv, fields


# noinspection PyAbstractClass
class Setor(osv.Model):
    """
    Classe que representa os campos do formulário Setor.
    """
    _name = 'ud.setor'
    _inherit = 'ud.setor'

    _columns = {
        'emite_portaria': fields.boolean('Emite portaria'),
        'responsavel_id': fields.many2one('ud.employee', u'Responśavel'),
    }


