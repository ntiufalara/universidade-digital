# encoding: UTF-8
from odoo import http


class DetalhesPublicacao(http.Controller):
    @http.route('/repositorio/publicacoes/<int:pub_id>', auth='public')
    def index(self, pub_id, **kwargs):
        Publicacao = http.request.env['ud.biblioteca.publicacao']
        pub = Publicacao.search([('id', '=', pub_id)])

        # incrementa visualizações
        plus = http.request.session.get('visualizacoes_plus')
        if not plus:
            http.request.session['visualizacoes_plus'] = ''
        if not str(pub_id) in http.request.session['visualizacoes_plus']:
            pub.visualizacoes_plus()
            http.request.session['visualizacoes_plus'] = http.request.session['visualizacoes_plus'] + '{},'.format(
                pub_id
            )
        return http.request.render('ud_biblioteca_website.detalhes_publicacao', {
            'pub': pub
        })
