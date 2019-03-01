# encoding: UTF-8

from odoo import models, fields


class AtualizaTitulacaoOrientador(models.TransientModel):
    _name = 'ud.biblioteca.atualizar_titulacao.orientador.wizard'

    titulacao_id = fields.Many2one('ud.biblioteca.orientador.titulacao', u'Titulação', required=True)

    def atualizar_titulacao(self):
        """
        Cria uma cópia do orientador e atualiza a titulaçãp
        """
        orientador_sel_ids = self._context.get('active_ids')
        orientador_model = self.env[self._context.get('active_model')]

        orientadores = orientador_model.browse(orientador_sel_ids)

        for orientador in orientadores:
            if not orientador.ativo:
                raise models.ValidationError(u'Desculpe, um ou mais orietadores selecionados não estão ativos')
            orientador.ativo = False
            orientador.copy({
                'titulacao_id': self.titulacao_id.id,
                'ativo': True,
                'publicacao_orientador_ids': [],
                'publicacao_coorientador_ids': [],
            })

        orientador = orientadores if len(orientadores) == 1 else False
        if orientador:
            return {
                'name': 'Orientador atualizado',
                'view_type': 'form',
                'view_mode': 'tree',
                'res_model': 'ud.biblioteca.publicacao.orientador',
                'view_id': self.env.ref('ud_biblioteca.ud_biblioteca_orientador_tree').id,
                'type': 'ir.actions.act_window',
                'target': 'current',
            }
