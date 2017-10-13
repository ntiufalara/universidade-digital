# encoding: UTF-8

from openerp.osv import osv, fields


# noinspection PyAbstractClass
class SubstituirPalavraChave(osv.TransientModel):
    _name = 'ud.biblioteca.substituir_palavra_chave.wizard'

    _columns = {
        'nova_palavra': fields.char(u'Nova palavra-chave', required=True),
    }

    def subistituir_palavra_chave(self, cr, uid, ids, context=None):
        """
        Cria uma nova palavra-chave, busca as publicações afetadas pelas palavras-chave selecionadas,
        remove as selecionadas, subistitui pela nova palavra-chave
        :param cr:
        :param uid:
        :param ids:
        :param context:
        :return:
        """
        context = {} if not context else context
        obj = self.browse(cr, uid, ids)[0]
        palavra_sel_ids = context.get('active_ids')
        pc_model = self.pool.get(context.get('active_model'))

        # localiza todas as publicações afetadas e remove a palavra antiga
        pub_afetadas = set()
        for palavra in pc_model.browse(cr, uid, palavra_sel_ids):
            for pub in palavra.publicacao_id:
                pub_afetadas.add(pub.id)
            pc_model.unlink(cr, uid, palavra.id)

        # Cria a nova palavra
        pc_model.create(cr, uid, {
            'name': obj.nova_palavra,
            'publicacao_id': [(4, p) for p in pub_afetadas]
        })
        return {}


