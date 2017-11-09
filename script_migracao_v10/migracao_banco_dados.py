# encoding: UTF-8

import xmlrpclib
import csv


def gera_csv(nome, dados=None):
    if type(dados) != list or not dados:
        raise Exception('É necessário passar uma lista com dados')

    with open(nome, 'w') as f:
        writer = csv.writer(f)
        cabecalhos = dados[0].keys()
        writer.writerow(cabecalhos)
        for instancia in dados:
            row = []
            for c in cabecalhos:
                row.append(unicode(instancia[c]).encode('utf-8'))
            writer.writerow(row)


def dados_campus(_server, _db, _uid, _password):
    campus_ids = _server.execute(_db, _uid, _password, 'ud.campus', 'search', [])
    campus = _server.execute(_db, _uid, _password, 'ud.campus', 'read', campus_ids)
    gera_csv('dados_campus.csv', campus)


def dados_polo(_server, _db, _uid, _password):
    polo_ids = _server.execute(_db, _uid, _password, 'ud.polo', 'search', [])
    polos = _server.execute(_db, _uid, _password, 'ud.polo', 'read', polo_ids)
    gera_csv('dados_polo.csv', polos)


def dados_espaco(_server, _db, _uid, _password):
    espaco_ids = _server.execute(_db, _uid, _password, 'ud.espaco', 'search', [])
    espacos = _server.execute(_db, _uid, _password, 'ud.espaco', 'read', espaco_ids)
    gera_csv('dados_espaco.csv', espacos)


def dados_bloco(_server, _db, _uid, _password):
    bloco_ids = _server.execute(_db, _uid, _password, 'ud.bloco', 'search', [])
    blocos = _server.execute(_db, _uid, _password, 'ud.bloco', 'read', bloco_ids)
    gera_csv('dados_bloco.csv', blocos)


def dados_setor(_server, _db, _uid, _password):
    setor_ids = _server.execute(_db, _uid, _password, 'ud.setor', 'search', [])
    setores = _server.execute(_db, _uid, _password, 'ud.setor', 'read', setor_ids)
    gera_csv('dados_setor.csv', setores)


# https://www.odoo.com/documentation/8.0/api_integration.html
# https://doc.odoo.com/6.1/developer/12_api/
# https://doc.odoo.com/6.1/developer/12_api/#python
def main(_url, _db, _username, _password):
    auth = xmlrpclib.ServerProxy("{}/xmlrpc/common".format(_url))
    uid = auth.login(_db, _username, _password)

    server = xmlrpclib.ServerProxy("{}/xmlrpc/object".format(_url))

    dados_campus(server, _db, uid, _password)
    dados_polo(server, _db, uid, _password)
    dados_espaco(server, _db, uid, password)
    dados_bloco(server, _db, uid, password)
    dados_setor(server, _db, uid, password)


if __name__ == "__main__":
    url, db, username, password = ['http://localhost:8069', "ud", "admin", "admin@ud&"]
    main(url, db, username, password)
