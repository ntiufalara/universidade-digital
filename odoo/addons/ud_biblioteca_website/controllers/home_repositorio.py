from odoo import http


class HomeRepositorio(http.Controller):
    @http.route('/repositorio/', auth='public')
    def index(self, **kwargs):
        Cursos = http.request.env['ud.curso']
        Pc = http.request.env['ud.biblioteca.p_chave']
        Publicacao = http.request.env['ud.biblioteca.publicacao']
        Polo = http.request.env['ud.polo']

        cursos_arapiraca = Cursos.search([('polo_id.campus_id.name', 'ilike', 'arapiraca')], order='name asc')
        palavras_chave = Pc.search([], order="write_date", limit=10)

        todos_cursos_arapiraca = Cursos.search([('polo_id.campus_id.name', 'ilike', 'arapiraca')], order='write_date')
        todas_palavras_chave = Pc.search([], order="write_date", limit=50)

        return http.request.render('ud_biblioteca_website.home_repositorio', {
            'cursos': cursos_arapiraca,
            'assuntos_count': '{:,}'.format(Pc.search_count([])).replace(',', '.'),
            'publicacoes_count': '{:,}'.format(Publicacao.search_count([])).replace(',', '.'),
            'unidades_count': Polo.search_count([]),
            'palavras_chave': palavras_chave,
            'todos_cursos_arapiraca': todos_cursos_arapiraca,
            'todas_palavras_chave': todas_palavras_chave
        })
