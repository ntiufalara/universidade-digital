# encoding: UTF-8
from copy import copy

from odoo import http
from odoo.addons.ud_biblioteca_website.controllers import utils


class ListaPublicacoesCurso(http.Controller):
    @http.route('/repositorio/publicacoes/', auth='public')
    def index(self, **kwargs):
        itens_per_page = 10
        Publicacao = http.request.env['ud.biblioteca.publicacao']

        # Monta a busca e os filtros
        publicacoes = Publicacao.search(self.make_domain(kwargs))

        Curso = http.request.env['ud.curso']
        Campus = http.request.env['ud.campus']
        Polo = http.request.env['ud.polo']
        CategoriaCNPQ = http.request.env['ud.biblioteca.publicacao.categoria_cnpq']
        TipoPublicacao = http.request.env['ud.biblioteca.publicacao.tipo']
        # Filtros
        cursos = Curso.search([])
        curso = Curso.search([('id', '=', kwargs.get('curso_id__id'))]) if kwargs.get('curso_id__id') else None
        campi = Campus.search([])
        campus = Campus.search([('id', '=', kwargs.get('campus_id__id'))]) if kwargs.get('campus_id__id') else None
        polos = Polo.search([])
        polo = Polo.search([('id', '=', kwargs.get('polo_id__id'))]) if kwargs.get('polo_id__id') else None
        tipos = TipoPublicacao.search([])
        tipo = TipoPublicacao.search([('id', '=', kwargs.get('tipo_id__id'))]) if kwargs.get('tipo_id__id') else None
        categorias_cnpq = CategoriaCNPQ.search([])
        categoria_cnpq = CategoriaCNPQ.search([('id', '=', kwargs.get('categoria_cnpq_id__id'))]) if kwargs.get(
            'categoria_cnpq_id__id') else None

        # Exibe lista de anos disponíveis para filtro
        anos = list({pub.ano_pub.strip() for pub in publicacoes})
        anos.sort(reverse=True)

        page_data = utils.paginacao(publicacoes, itens_per_page, kwargs.get('page_num'))
        context = {
            'publicacoes': publicacoes[page_data.get('start'):page_data.get('end')],
            'campi': campi,
            'campus': campus,
            'cursos': cursos,
            'curso': curso,
            'anos': anos,
            'ano': kwargs.get('ano_pub'),
            'polos': polos,
            'polo': polo,
            'tipos': tipos,
            'tipo': tipo,
            'categorias_cnpq': categorias_cnpq,
            'categoria_cnpq': categoria_cnpq
        }
        context.update(page_data)

        return http.request.render('ud_biblioteca_website.publicacoes', context)

    def make_search(self, params):
        """
        Monta os parâmetros usando os valores dos checkbox prefixados com 'q_' e o valor de 'q=string'
        Exemplo:
        Se
            {
                'q_titulo': 'on',
                'q_autor__name': 'on'
            }
        e
            {
                'q': "rotinas administrativas"
            }
        converte para
            {
                'titulo': 'rotinas administrativas',
                'autor__name': 'rotinas administrativas'
            }
        """
        for k in params:
            if k.startswith('q_'):
                params.pop(k)
                new_k = k.replace('q_', '')
                params[new_k] = params.get('q')

    def make_domain(self, query):
        """
        Transforma os parâmetros da querystring em um domain Odoo
        """
        params = copy(query)
        if 'q' in params:
            # Executa a conversão para o campo de busca
            self.make_search(params)
            params.pop('q')
        if 'page_num' in params:
            params.pop('page_num')
        domain_and = []
        domain_or = []
        # Curso
        for p in params:
            if params.get(p):
                # Converte a notação __ para .
                # Ex: ('curso_id__id', '=', 1) => ('curso_id.id', '=', 1)
                attribute = p.replace('__', '.')
                if params.get(p).isdigit():
                    # Parâmetros de filtro são convertidos para condições 'AND'
                    condition = (attribute, '=', params.get(p))
                    domain_and.append(condition)
                else:
                    # Parâmetros de busca são convertidos para condições 'OR'
                    condition = (attribute, 'ilike', params.get(p))
                    domain_or.append(condition)
        if domain_or:
            # Junta os domains de 'AND' e 'OR', adicionando o operador '|' a cada condição OR
            # uasndo a notação 'Polish'
            for i in range(len(domain_or) - 1):
                domain_and.append('|')
            domain_and.extend(domain_or)
        return domain_and
