# encoding: UTF-8
import logging
import re
from os.path import dirname, join

import simplejson as simplejson

from openerp.addons.web import http
from openerp.addons.web.controllers import main

import jinja2

_logger = logging.getLogger(__name__)


class CadastroMonitoria(http.Controller):
    _cp_path = '/cadastro_monitoria'

    # Os mesmos campos disponníveis no formulário, para validação
    campos = ['nome_completo', 'matricula', 'cpf', 'rg', 'email', 'celular', 'campus', 'polo',
              'curso', 'senha', 'confirma_senha']

    template_dir = join(dirname(dirname(__file__)), 'static', 'src', 'html')
    jinja2_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_dir),
        # autoescape=select_autoescape(['html', 'xml'])
    )

    @http.httprequest
    def index(self, req, **kwargs):
        template = self.jinja2_env.get_template('cadastro_monitoria.html')
        # Autentica o usuário anônimo para buscar por avisos no banco de dados
        db, user, password = 'ud', 'anonymous', 'anonymous'
        main.Session().authenticate(req, db, user, password)
        # busca os campi para adicionar ao select do formulário
        Campus = req.session.model('ud.campus')
        campi = Campus.read(Campus.search([]))
        if req.httprequest.method == 'GET':
            cadastro_ativo = True
            # Busca os cursos no núcleo
            return template.render({
                'cadastro_ativo': cadastro_ativo,
                'campi': campi,
                'values': kwargs,
            })
        elif req.httprequest.method == 'POST':
            try:
                # Valida todos os campos
                self.validate(kwargs)
                # Conclui o cadastro
                # User = req.session.model('res.users')
                Pessoa = req.session.model('ud.employee')
                # Perfil = req.session.model('ud.perfil')

                # Busca pelo grupo de permissões "Monitor/Tutor"
                ir_model_obj = req.session.model('ir.model.data')
                grupo_monitor_recs = ir_model_obj.get_object_reference('base', 'usuario_ud')
                grupo_monitor = grupo_monitor_recs and grupo_monitor_recs[1] or False
                _logger.info(u'Carregando...')
                # usuario = User.create({
                #     'email': kwargs.get('email'),
                #     'login': kwargs.get('login'),
                #     'password': kwargs.get('senha'),
                #     'name': kwargs.get('nome_completo'),
                #     'groups_id': [[5], [4, grupo_monitor]]
                # })
                #
                # _logger.info(u'Usuário cadastrado')

                pessoa = Pessoa.cria_pessoa_grupo(kwargs, grupo_monitor)

                # _logger.info(u'Pessoa cadastrado')
                #
                # Perfil.create({
                #     'tipo': 'a',
                #     'matricula': kwargs.get('matricula'),
                #     'ud_cursos': kwargs.get('curso'),
                #     'ud_papel_id': pessoa
                # }, {'ud_employee': pessoa})

                return template.render({
                    'campi': campi,
                    'sucesso': True,
                    'values': kwargs
                })
            except ValueError as e:
                return template.render({
                    'campi': campi,
                    'erro': e.message,
                    'values': kwargs
                })
            except Exception as e:
                _logger.error(e)
                return template.render({
                    'campi': campi,
                    'erro': u"Aconteceu um erro inesperado, por favor, entre em contato com o NTI do Campus Arapiraca "
                            u"para mais informações. marcos.neto@nti.ufal.br",
                    'values': kwargs
                })

    def validate(self, data):
        for campo in self.campos:
            if not data.get(campo):
                raise ValueError(u"O campo: {} é obrigatório".format(campo.capitalize().replace('_', ' ')))
        # verificando nome completo
        if data.get('nome_completo') and len(data.get('nome_completo').split(' ')) < 2:
            raise ValueError(u'O nome completo precisa ter mais de uma palavra.')

        # valida CPF
        Utils.validar_cpf(data.get('cpf').decode('UTF-8').replace('.', '').replace('-', ''))
        data['login'] = data.get('cpf').decode('UTF-8').replace('.', '').replace('-', '')
        # valida o número de telefone
        if len(data.get('celular')) < 11:
            raise ValueError(u'Verifique se o número de celular está correto e tente novamente')
        if data.get('outro_telefone') and len(data.get('outro_telefone')) < 10:
            raise ValueError(u'Verifique se o número no campo "Outro telefone" está correto e tente novamente')
        # valida senhas
        if data.get('senha') != data.get('confirma_senha'):
            raise ValueError(u'A confirmação de senha não confere, a senha e a confirmação deve ser iguais')
        Utils.validate_password(data.get('senha'))


class FiltrarLocalJson(http.Controller):
    _cp_path = '/ud_monitoria_cadastro/filtrar_local'

    @http.httprequest
    def polo(self, req, **kwargs):
        # Autentica o usuário anônimo para buscar por avisos no banco de dados
        db, user, password = 'ud', 'anonymous', 'anonymous'
        main.Session().authenticate(req, db, user, password)
        # Busca os polos de acordo com o Campus passado como parâmetro
        Polo = req.session.model('ud.polo')
        polos = Polo.read(
            Polo.search([('campus_id', '=', int(kwargs.get('campus_id')))])
        )
        return simplejson.dumps(polos)

    @http.httprequest
    def curso(self, req, **kwargs):
        # Autentica o usuário anônimo para buscar por avisos no banco de dados
        db, user, password = 'ud', 'anonymous', 'anonymous'
        main.Session().authenticate(req, db, user, password)
        # Busca os polos de acordo com o Campus passado como parâmetro
        Curso = req.session.model('ud.curso')
        cursos = Curso.read(
            Curso.search([('polo_id', '=', int(kwargs.get('polo_id')))])
        )
        return simplejson.dumps(cursos)


class Utils(object):
    @staticmethod
    def validate_password(senha):
        """
        Validate password algorithm
        """
        if len(senha) < 8:
            raise ValueError(u"A senha precisa ter mais de %d digitos" % 8)
        elif not re.search(r'[^\d]', senha) and re.search(r'\d', senha):
            raise ValueError(u'A senha precisa possuir números e letras')

    @staticmethod
    def validar_cpf(cpf):
        """
        Valida CPFs
        """

        def calcula_dv1(_cpf):
            start = 10
            cpf_list = [int(i) for i in _cpf]
            soma = 0
            for i in cpf_list[:-2]:
                val = i * start
                soma += val
                start -= 1
            resto = soma % 11
            _dv1 = 11 - resto
            if resto < 2:
                _dv1 = 0
            return _dv1

        def calcula_dv2(_cpf):
            start = 11
            cpf_list = [int(i) for i in _cpf]
            soma = 0
            for i in cpf_list[:-1]:
                val = i * start
                soma += val
                start -= 1
            resto = soma % 11
            _dv2 = 11 - resto
            if resto < 2:
                _dv2 = 0
            return _dv2

        if len(cpf) == 11:
            dv1 = calcula_dv1(cpf)
            dv2 = calcula_dv2(cpf)
            if int(cpf[-2]) != dv1 or int(cpf[-1]) != dv2 or cpf[1:] == cpf[:-1]:
                raise ValueError('CPF Inválido')
        else:
            raise ValueError('CPF não contém 11 digitos')
