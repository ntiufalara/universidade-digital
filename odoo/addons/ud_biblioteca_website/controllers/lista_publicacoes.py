# encoding: UTF-8
from odoo import http
from odoo.addons.ud_biblioteca_website.controllers import utils


class ListaPublicacoesCurso(http.Controller):
    @http.route('/repositorio/publicacoes/', auth='public')
    def index(self, **kwargs):
        itens_per_page = 10
        Publicacao = http.request.env['ud.biblioteca.publicacao']

        # Filtra e lista por curso
        Curso = http.request.env['ud.curso']
        curso = None
        cursos = Curso.search([])
        if kwargs.get('curso_id'):
            publicacoes = Publicacao.search([('curso_id.id', '=', kwargs.get('curso_id'))])
            curso = cursos.search([('id', '=', kwargs.get('curso_id'))])
        else:
            publicacoes = Publicacao.search([])

        # Filtra lista por ano
        if kwargs.get('ano'):
            cursos = cursos.search([('publicacao_ids.ano_pub', '=', kwargs.get('ano'))])
            publicacoes = publicacoes & Publicacao.search([('ano_pub', '=', kwargs.get('ano'))])

        # Filtra lista por ano
        if kwargs.get('p_chave'):
            cursos = cursos.search([('publicacao_ids.palavras_chave_ids.id', '=', kwargs.get('p_chave'))])
            publicacoes = publicacoes & Publicacao.search([('palavras_chave_ids.id', '=', kwargs.get('p_chave'))])

        # Filtra e lista por busca
        if kwargs.get('q'):
            busca = kwargs.get('q')
            # Pesquisa principal 'Intercessão com filtros anteriores'
            publicacoes2 = Publicacao.search([('name', 'ilike', busca)])
            # Pesquisas secundárias 'União com pesquisa principal'
            # Busca primeiro pelo autor, depois pela palavra-chave
            publicacoes2 = publicacoes2 | Publicacao.search([('autor_id.name', 'ilike', busca)])
            publicacoes2 = publicacoes2 | Publicacao.search([('palavras_chave_ids.name', 'ilike', busca), ])
            # Buscar por quaisquer outras correspondências
            publicacoes2 = publicacoes2 | Publicacao.search([
                '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|',
                ('autor_id.ultimo_nome', 'ilike', busca),
                ('ano_pub', 'ilike', busca),
                ('campus_id.name', 'ilike', busca),
                ('polo_id.name', 'ilike', busca),
                ('curso_id.name', 'ilike', busca),
                ('orientador_ids.name', 'ilike', busca),
                ('orientador_ids.ultimo_nome', 'ilike', busca),
                ('coorientador_ids.name', 'ilike', busca),
                ('coorientador_ids.ultimo_nome', 'ilike', busca),
                ('tipo_id.name', 'ilike', busca),
                ('categoria_cnpq_id.name', 'ilike', busca),
                ('area_ids.name', 'ilike', busca),
            ])
            publicacoes = publicacoes & publicacoes2 if publicacoes else publicacoes2

        # Exibe lista de anos disponíveis para filtro
        anos = list({pub.ano_pub for pub in publicacoes})

        page_data = utils.paginacao(publicacoes, itens_per_page, kwargs.get('page_num'))
        context = {
            'publicacoes': publicacoes[page_data.get('start'):page_data.get('end')],
            'cursos': cursos,
            'anos': anos,
            'ano': kwargs.get('ano'),
            'curso': curso
        }
        context.update(page_data)

        return http.request.render('ud_biblioteca_website.publicacoes', context)
