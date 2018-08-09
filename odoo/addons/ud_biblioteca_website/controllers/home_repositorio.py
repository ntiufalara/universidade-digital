from odoo import http

# Busca em todos os campos
"""
filter_domain="[
'|', '|', '|', '|', '|', ('x_mfrname1','ilike',self), ('x_mfrname2','ilike',self), ('x_mfrname3','ilike',self), ('x_mfrname4','ilike',self), ('x_mfrname5','ilike',self), ('x_mfrname5','ilike',self)
]"
"""


class HomeRepositorio(http.Controller):
    @http.route('/repositorio/', auth='public')
    def index(self, **kwargs):
        Cursos = http.request.env['ud.curso']
        Pc = http.request.env['ud.biblioteca.p_chave']

        cursos_arapiraca = Cursos.search([('polo_id.campus_id.name', 'ilike', 'arapiraca')], order='write_date',
                                         limit=10)
        palavras_chave = Pc.search([], order="write_date", limit=10)
        return http.request.render('ud_biblioteca_website.home_repositorio', {
            'cursos': cursos_arapiraca,
            'palavras_chave': palavras_chave,
        })
