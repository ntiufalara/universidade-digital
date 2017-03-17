# coding: utf-8
"""
Métodos de validação de ud_employee que NÃO estão sendo utilizados foram movidos para esse arquivo.
"""
import re


def _valida_rg(cls, cr, uid, ids, context=None):
    """
    Método que valida os campos do formulário Pessoa. Ex.: RG:111111 (sem traços).
    return: False se dados passados estão fora desse padrão ou True, caso contrário.
    """
    record = cls.browse(cr, uid, ids, context=None)
    for data in record:
        if not re.match("^-?[0-9]+$", data.rg):
            return True
    else:
        return False
    return True


def _valida_telefone(cls, cr, uid, ids, context=None):
    """
    Método que valida os campos do formulário Pessoa. Ex.: Telefone Residencial:111111 (somente números).
    return: False se dados passados estão fora desse padrão ou True, caso contrário.
    """
    record = cls.browse(cr, uid, ids, context=None)
    try:
        for data in record:
            if re.match("^-?[0-9]+$", data.work_phone):
                return True
        else:
            return False
    except TypeError:
        pass
    return True

def _valida_celular(cls, cr, uid, ids, context=None):
    """
    Método que valida os campos do formulário Pessoa. Ex.: Telefone Celular:111111 (somente números).
    return: False se dados passados estão fora desse padrão ou True, caso contrário.
    """
    record = cls.browse(cr, uid, ids, context=None)
    for data in record:
        if not re.match("^-?[0-9]+$", data.mobile_phone):
            return True
        else:
            return False
    return True