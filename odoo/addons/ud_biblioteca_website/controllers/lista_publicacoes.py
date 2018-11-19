# encoding: UTF-8
from copy import copy

from odoo import http
from odoo.addons.ud_biblioteca_website.controllers import utils


class ListaPublicacoesCurso(http.Controller):
    @http.route('/repositorio/publicacoes/', auth='public')
    def index(self, **kwargs):
        itens_per_page = 10
        Publicacao = http.request.env['ud.biblioteca.publicacao']

        publicacoes = Publicacao.search(self.make_domain(kwargs))

        Curso = http.request.env['ud.curso']
        Campus = http.request.env['ud.campus']
        Polo = http.request.env['ud.polo']
        TipoPublicacao = http.request.env['ud.biblioteca.publicacao.tipo']
        cursos = Curso.search([])
        curso = Curso.search([('id', '=', kwargs.get('curso_id__id'))]) if kwargs.get('curso_id__id') else None
        campi = Campus.search([])
        campus = Campus.search([('id', '=', kwargs.get('campus_id__id'))]) if kwargs.get('campus_id__id') else None
        polos = Polo.search([])
        polo = Polo.search([('id', '=', kwargs.get('polo_id__id'))]) if kwargs.get('polo_id__id') else None
        tipos = TipoPublicacao.search([])
        tipo = TipoPublicacao.search([('id', '=', kwargs.get('tipo_id__id'))]) if kwargs.get('tipo_id__id') else None

        # Exibe lista de anos disponíveis para filtro
        anos = list({pub.ano_pub for pub in publicacoes})

        page_data = utils.paginacao(publicacoes, itens_per_page, kwargs.get('page_num'))
        context = {
            'publicacoes': publicacoes[page_data.get('start'):page_data.get('end')],
            'campi': campi,
            'campus': campus,
            'cursos': cursos,
            'curso': curso,
            'anos': anos,
            'ano': kwargs.get('ano'),
            'polos': polos,
            'polo': polo,
            'tipos': tipos,
            'tipo': tipo
        }
        context.update(page_data)

        return http.request.render('ud_biblioteca_website.publicacoes', context)

    def make_domain(self, query):
        params = copy(query)
        if 'q' in params:
            params.pop('q')
        domain_and = []
        domain_or = []
        # Curso
        for p in params:
            if params.get(p):
                # Converte a notação __ para .
                # Ex: ('curso_id__id', '=', 1) => ('curso_id.id', '=', 1)
                attribute = p.replace('__', '.')
                if params.get(p).isdigit():
                    condition = (attribute, '=', params.get(p))
                    domain_and.append(condition)
                else:
                    condition = (attribute, 'ilike', params.get(p))
                    domain_or.append(condition)
        print(domain_or)
        if domain_or:
            for i in range(len(domain_or) - 1):
                domain_and.append('|')
            domain_and.extend(domain_or)
        print(domain_and)
        return domain_and
