# encoding: UTF-8

from openerp.osv import osv, fields


# noinspection PyAbstractClass
class SubstituirPalavraChave(osv.TransientModel):
    _name = 'ud.biblioteca.substituir_palavra_chave.wizard'

    _columns = {
        'nova_palavra': fields.char(u'Nova palavra-chave', required=True),
        'palavras_substituidas': fields.many2many('ud.biblioteca.pc', 'substituir_pc_wizard',
                                                  string=u'Palavras substituídas')
    }
