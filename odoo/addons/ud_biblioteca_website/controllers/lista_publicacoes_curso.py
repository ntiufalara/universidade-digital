from odoo import http


class ListaPublicacoesCurso(http.Controller):
    @http.route('/repositorio/publicacoes/', auth='public')
    def index(self, **kwargs):
        domain = [
            ('curso_id.polo_id.campus_id.name', 'ilike', 'arapiraca')
        ]
        if 'curso' in kwargs:
            print(kwargs)
        Publicacao = http.request.env['ud.biblioteca.publicacao']
        publicacoes = Publicacao.search(domain)
        return http.request.render('ud_biblioteca_website.publicacoes', {
            'publicacoes': publicacoes
        })
