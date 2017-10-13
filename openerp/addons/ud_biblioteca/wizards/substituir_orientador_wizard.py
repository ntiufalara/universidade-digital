# encoding: UTF-8

from openerp.osv import osv, fields


# noinspection PyAbstractClass
class SubstituirOrientador(osv.TransientModel):
    _name = 'ud.biblioteca.substituir_orientador.wizard'

    _columns = {
        'novo_orientador': fields.char(u'Novo orientador', required=True),
    }

    def subistituir_orientador(self, cr, uid, ids, context=None):
        """
        Cria um novo orientador, busca as publicações afetadas pelo orientador selecionada,
        remove as selecionadas, subistitui pela novo orientador
        :param cr:
        :param uid:
        :param ids:
        :param context:
        :return:
        """
        context = {} if not context else context
        obj = self.browse(cr, uid, ids)[0]
        orientador_sel_ids = context.get('active_ids')
        orientador_model = self.pool.get(context.get('active_model'))

        # localiza todas as publicações afetadas e remove a palavra antiga
        pub_afetadas_orientador = set()
        pub_afetadas_coorientador = set()
        for orientador in orientador_model.browse(cr, uid, orientador_sel_ids):
            for pub in orientador.publicacao_orientador_id:
                pub_afetadas_orientador.add(pub.id)
            for pub in orientador.publicacao_coorientador_id:
                pub_afetadas_coorientador.add(pub.id)
            orientador_model.unlink(cr, uid, orientador.id)

        # Cria o novo orientador
        orientador_model.create(cr, uid, {
            'name': obj.novo_orientador,
            'publicacao_orientador_id': [(4, p) for p in pub_afetadas_orientador],
            'publicacao_coorientador_id': [(4, p) for p in pub_afetadas_coorientador],
        })
        return {}


