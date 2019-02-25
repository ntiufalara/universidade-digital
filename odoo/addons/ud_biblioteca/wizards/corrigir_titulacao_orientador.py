# encoding: UTF-8
from odoo import models, fields


class CorrigirTitulacaoOrientador(models.TransientModel):
    _name = 'ud.biblioteca.corrigir_titulacao.orientador.wizard'

    titulacao_id = fields.Many2one('ud.biblioteca.orientador.titulacao', u'Titulação', required=True)

    def substituir_titulacao(self):
        """
        Substitui a titulação dos orientadores selecionados
        """
        orientador_sel_ids = self._context.get('active_ids')
        orientador_model = self.env[self._context.get('active_model')]

        for orientador in orientador_model.browse(orientador_sel_ids):
            orientador.titulacao_id = self.titulacao_id.id
