# encoding: UTF-8
from __future__ import unicode_literals

import re


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
