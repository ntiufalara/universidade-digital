# encoding: UTF-8

import xmlrpclib
import csv
import pprint


def gera_csv(nome, dados=None):
    if type(dados) != list or not dados:
        raise Exception('É necessário passar uma lista com dados')

    with open(nome, 'w') as f:
        writer = csv.writer(f, delimiter=';')
        cabecalhos = dados[0].keys()
        writer.writerow(cabecalhos)
        for instancia in dados:
            row = []
            for c in cabecalhos:
                instancia[c] = instancia[c] if instancia[c] != [] else ""
                row.append(unicode(instancia[c]).encode('UTF-8'))
            writer.writerow(row)


def process_relations(obj):
    for field in obj:
        if type(obj[field]) is list and len(obj[field]) == 2:
            obj[field] = obj[field][1]


def replace_id(key_name, recordset, p):
    # Substitui o id do orientador pela lista de nomes em string (CSV)
    result_str = u''
    p[key_name] = [p[key_name]] if type(p[key_name]) != list else p[key_name]
    for o_id in p[key_name]:
        # Busca no recordset dos orientadores
        for o in recordset:
            if o['id'] == o_id:
                result_str += u'"{}",'.format(o['name']) if p[key_name].index(o_id) != len(
                    p[key_name]) - 1 else u'"{}"'.format(o['name'])
    # result_str += u''
    return result_str


def dump_publicacoes(server, _db, uid, _password):
    p_chave_ids = server.execute(_db, uid, _password, 'ud.biblioteca.pc', 'search', [])
    orentadores_ids = server.execute(_db, uid, _password, 'ud.biblioteca.orientador', 'search', [])
    obj_ids = server.execute(_db, uid, _password, 'ud.biblioteca.publicacao', 'search', [])

    p_chave = server.execute_kw(_db, uid, _password, 'ud.biblioteca.pc', 'read', [p_chave_ids])
    orientadores = server.execute_kw(_db, uid, _password, 'ud.biblioteca.orientador', 'read', [orentadores_ids])
    pub = server.execute_kw(_db, uid, _password,
                            'ud.biblioteca.publicacao', 'read', [obj_ids],
                            )

    for p in pub:
        process_relations(p)
        orientador_str = replace_id('orientador_ids', orientadores, p)
        p['orientador_ids'] = orientador_str
        coorientador_str = replace_id('coorientador_ids', orientadores, p)
        p['coorientador_ids'] = coorientador_str
        p_chave_str = replace_id('palavras_chave_ids', p_chave, p)
        p['palavras_chave_ids'] = p_chave_str
    pprint.pprint(pub[len(pub) - 1])

    gera_csv('publicacoes.csv', pub)


def main(_url, _db, _username, _password):
    auth = xmlrpclib.ServerProxy("{}/xmlrpc/common".format(_url))
    uid = auth.login(_db, _username, _password)

    server = xmlrpclib.ServerProxy("{}/xmlrpc/object".format(_url))

    dump_publicacoes(server, _db, uid, _password)


if __name__ == "__main__":
    url, db, username, password = ['http://localhost:8009', "ud", "admin", "admin@ud&"]
    main(url, db, username, password)
