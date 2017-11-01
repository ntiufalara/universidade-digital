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
                if type(instancia[c]) is str:
                    print instancia[c]
                    row.append(unicode(instancia[c]).encode('utf-8'))
                else:
                    row.append(instancia[c])
            writer.writerow(row)


def dados_campus(_server, _db, _uid, _password):
    campus_ids = _server.execute(_db, _uid, _password, 'ud.campus', 'search', [])
    campus = _server.execute(_db, _uid, _password, 'ud.campus', 'read', campus_ids)
    gera_csv('dados_campus.csv', campus)


def dados_polo(_server, _db, _uid, _password):
    polo_ids = _server.execute(_db, _uid, _password, 'ud.polo', 'search', [])
    polos = _server.execute(_db, _uid, _password, 'ud.polo', 'read', polo_ids)
    gera_csv('dados_polo.csv', polos)


# https://www.odoo.com/documentation/8.0/api_integration.html
# https://doc.odoo.com/6.1/developer/12_api/
# https://doc.odoo.com/6.1/developer/12_api/#python
def main(_url, _db, _username, _password):
    auth = xmlrpclib.ServerProxy("{}/xmlrpc/common".format(_url))
    uid = auth.login(_db, _username, _password)

    server = xmlrpclib.ServerProxy("{}/xmlrpc/object".format(_url))

    dados_campus(server, _db, uid, _password)
    dados_polo(server, _db, uid, _password)


if __name__ == "__main__":
    url, db, username, password = ['http://localhost:8069', "ud", "admin", "admin@ud&"]
    main(url, db, username, password)
