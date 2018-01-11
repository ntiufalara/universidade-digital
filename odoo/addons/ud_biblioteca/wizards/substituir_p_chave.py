# encoding: UTF-8

from odoo import models, fields, api


class SubstituirPChave(models.TransientModel):
    _name = 'ud.biblioteca.substituir_palavra_chave.wizard'

    nova_palavra = fields.Char(u'Nova palavra-chave', required=True)

    def substituir_palavra_chave(self):
        """
        Cria uma nova palavra-chave, busca as publicações afetadas pelas palavras-chave selecionadas,
        remove as selecionadas, subistitui pela nova palavra-chave
        :return:
        """
        palavra_sel_ids = self._context.get('active_ids')
        pc_model = self.env[self._context.get('active_model')]

        # localiza todas as publicações afetadas e remove a palavra antiga
        pub_afetadas = set()
        for palavra in pc_model.browse(palavra_sel_ids):
            for pub in palavra.publicacao_id:
                pub_afetadas.add(pub.id)
            palavra.unlink()

        # Cria a nova palavra
        pc_model.create({
            'name': self.nova_palavra,
            'publicacao_id': [(4, p) for p in pub_afetadas]
        })
        return {}
