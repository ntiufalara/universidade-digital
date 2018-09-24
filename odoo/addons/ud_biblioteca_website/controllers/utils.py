# encoding: UTF-8
import math


def paginacao(objs, itens_per_page, page_num=None):
    """
    Cria um dicionário de dados de paginação
    :param objs: RecordSet de objetos para paginar
    :param itens_per_page: int: Quantidade de itens por página
    :param page_num: int: Número da página atual
    :return:
    """
    page_num = 1 if not page_num else int(page_num)
    end = page_num * itens_per_page
    start = end - itens_per_page
    last_page = int(math.ceil(len(objs) / float(itens_per_page)))
    prev_page = page_num - 1 if page_num - 1 > 0 else None
    next_page = page_num + 1 if page_num + 1 <= last_page else None

    return {
        'start': start,
        'end': end,
        'page_num': page_num,
        'last_page': last_page,
        'prev_page': prev_page,
        'next_page': next_page,
    }
