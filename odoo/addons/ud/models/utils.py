# encoding: UTF-8
BANCOS = [
    ('218', u'218 - Banco Bonsucesso S.A.'), ('036', u'036 - Banco Bradesco BBI S.A'),
    ('204', u'204 - Banco Bradesco Cartões S.A.'), ('237', u'237 - Banco Bradesco S.A.'),
    ('263', u'263 - Banco Cacique S.A.'), ('745', u'745 - Banco Citibank S.A.'),
    ('229', u'229 - Banco Cruzeiro do Sul S.A.'), ('001', u'001 - Banco do Brasil S.A.'),
    ('047', u'047 - Banco do Estado de Sergipe S.A.'), ('037', u'037 - Banco do Estado do Pará S.A.'),
    ('041', u'041 - Banco do Estado do Rio Grande do Sul S.A.'), ('004', u'004 - Banco do Nordeste do Brasil S.A.'),
    ('184', u'184 - Banco Itaú BBA S.A.'), ('479', u'479 - Banco ItaúBank S.A'),
    ('479A', u'479A - Banco Itaucard S.A.'), ('M09', u'M09 - Banco Itaucred Financiamentos S.A.'),
    ('389', u'389 - Banco Mercantil do Brasil S.A.'), ('623', u'623 - Banco Panamericano S.A.'),
    ('633', u'633 - Banco Rendimento S.A.'), ('453', u'453 - Banco Rural S.A.'),
    ('422', u'422 - Banco Safra S.A.'), ('033', u'033 - Banco Santander (Brasil) S.A.'),
    ('073', u'073 - BB Banco Popular do Brasil S.A.'), ('104', u'104 - Caixa Econômica Federal'),
    ('477', u'477 - Citibank N.A.'), ('399', u'399 - HSBC Bank Brasil S.A. – Banco Múltiplo'),
    ('652', u'652 - Itaú Unibanco Holding S.A.'), ('341', u'341 - Itaú Unibanco S.A.'),
    ('409', u'409 - UNIBANCO – União de Bancos Brasileiros S.A.'),
]

TURNO = [("d", u"Diurno"), ("m", u"Matutino"),
         ("v", u"Vespertino"), ("n", u"Noturno"),
         ('i', u'Integral')]
MODALIDADE = [("l", u"Licenciatura"), ("b", u"Bacharelado"), ('e', u'Especialização'), ('m', u'Mestrado'), ('d', u'')]

NACIONALIDADES = [
    ('al', u'Alemã'), ('es', u'Espanhola'), ('fr', u'Francesa'), ('gr', u'Grega'), ('h', u'Húngaro'),
    ('ir', u'Irlandesa'), ('it', u'Italiana'), ('ho', u'Holandesa'), ('pt', u'Portuguesa'), ('in', u'Inglesa'),
    ('rs', u'Russa'), ('ar', u'Argentina'), ('br', u'Brasileira'), ('ch', u'Chilena'), ('e', u'Norte-Americana'),
    ('mx', u'Mexicana'), ('chi', u'Chinesa'), ('jp', u'Japonesa'), ('sf', u'Sul-Africana'), ('as', u'Australiana')
]
ESTADOS = [
    ('ac', u'AC'), ('al', u'AL'), ('ap', u'AP'), ('am', u'AM'), ('ba', u'BA'), ('ce', u'CE'), ('df', u'DF'),
    ('es', u'ES'), ('go', u'GO'), ('ma', u'MA'), ('mg', u'MG'), ('ms', u'MS'), ('mt', u'MT'), ('pa', u'PA'),
    ('pe', u'PE'), ('pi', u'PI'), ('pr', u'PR'), ('rj', u'RJ'), ('rn', u'RN'), ('ro', u'RO'), ('rr', u'RR'),
    ('rs', u'RS'), ('sc', u'SC'), ('se', u'SE'), ('sp', u'SP'), ('to', u'TO')
]


def validar_cpf_cnpj(cpf_cnpj):
    if len(cpf_cnpj) == 11:
        return validar_cpf(cpf_cnpj)
    elif len(cpf_cnpj) == 14:
        return validar_cnpj(cpf_cnpj)
    else:
        return False


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
            return False
    else:
        return False
    return True


def validar_cnpj(cnpj):
    """
    Valida CNPJs, retornando apenas a string de números válida.
    """
    cnpj = ''.join(re.findall('\d', str(cnpj)))

    if (not cnpj) or (len(cnpj) < 14):
        return False

    # Pega apenas os 12 primeiros dígitos do CNPJ e gera os 2 dígitos que faltam
    inteiros = map(int, cnpj)
    novo = inteiros[:12]

    prod = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    while len(novo) < 14:
        r = sum([x * y for (x, y) in zip(novo, prod)]) % 11
        if r > 1:
            f = 11 - r
        else:
            f = 0
        novo.append(f)
        prod.insert(0, 6)

    # Se o número gerado coincidir com o número original, é válido
    if novo != inteiros:
        return False
    return True
