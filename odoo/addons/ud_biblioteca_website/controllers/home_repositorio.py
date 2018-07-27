from odoo import http


class HomeRepositorio(http.Controller):
    @http.route('/repositorio/', auth='public')
    def index(self, **kwargs):
        Cursos = http.request.env['ud.curso']
        Pc = http.request.env['ud.biblioteca.p_chave']

        cursos_arapiraca = Cursos.search([('polo_id.campus_id.name', 'ilike', 'arapiraca')], order='name')
        palavras_chave = Pc.search([])
        return http.request.render('ud_biblioteca_website.home_repositorio', {
            'cursos': cursos_arapiraca,
            'palavras_chave': palavras_chave,
        })
