# encoding: UTF-8

from odoo import models, fields, api


class SubstituirOrientador(models.TransientModel):
    _name = 'ud.biblioteca.substituir_orientador.wizard'

    novo_orientador = fields.Char(u'Nome', required=True)
    ultimo_nome = fields.Char(u'Último nome', required=True)
    titulacao_id = fields.Many2one('ud.biblioteca.orientador.titulacao', u'Titulação', required=True)

    def substituir_orientador(self):
        """
        Cria um novo orientador, busca as publicações afetadas pelo orientador selecionada,
        remove as selecionadas, subistitui pela novo orientador
        :return:
        """
        orientador_sel_ids = self._context.get('active_ids')
        orientador_model = self.env[self._context.get('active_model')]

        # localiza todas as publicações afetadas e remove a palavra antiga
        pub_afetadas_orientador = set()
        pub_afetadas_coorientador = set()
        for orientador in orientador_model.browse(orientador_sel_ids):
            for pub in orientador.publicacao_orientador_ids:
                pub_afetadas_orientador.add(pub.id)
            for pub in orientador.publicacao_coorientador_ids:
                pub_afetadas_coorientador.add(pub.id)
            orientador.unlink()

        # Cria o novo orientador
        orientador_model.create({
            'name': self.novo_orientador,
            'ultimo_nome': self.ultimo_nome,
            'titulacao_id': self.titulacao_id.id,
            'publicacao_orientador_ids': [(4, p) for p in pub_afetadas_orientador],
            'publicacao_coorientador_ids': [(4, p) for p in pub_afetadas_coorientador],
        })
        return {}
