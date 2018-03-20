# encoding: UTF-8
import re
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
                row.append(unicode(instancia[c]).encode('UTF-8'))
            writer.writerow(row)


def process_relations(obj):
    for field in obj:
        if type(obj[field]) is list and len(obj[field]) == 2:
            obj[field] = obj[field][1]


def dump_module_data(_server, _db, _uid, _password, _module):
    models_ids = _server.execute(_db, _uid, _password, 'ir.model', 'search', [])
    models = _server.execute(_db, _uid, _password, 'ir.model', 'read', models_ids)
    module_models = []

    # Filtra apenas os models do módulo em questão
    for model in models:
        if _module in model.get('modules').split(','):
            module_models.append(model)

    for model in module_models:
        if model.get('model') == 'ud.biblioteca.anexo':
            continue
        print ">> Model: {}".format(model.get('model'))
        objs = []
        try:
            obj_ids = _server.execute(_db, _uid, _password, model.get('model'), 'search', [])
        except:
            continue
        for obj_id in obj_ids:
            obj = _server.execute(_db, _uid, _password, model.get('model'), 'read', obj_id)
            process_relations(obj)
            objs.append(obj)
        if objs:
            gera_csv(model.get('model')+'.csv', objs)


# https://www.odoo.com/documentation/8.0/api_integration.html
# https://doc.odoo.com/6.1/developer/12_api/
# https://doc.odoo.com/6.1/developer/12_api/#python
def main(_url, _db, _username, _password):
    auth = xmlrpclib.ServerProxy("{}/xmlrpc/common".format(_url))
    uid = auth.login(_db, _username, _password)

    server = xmlrpclib.ServerProxy("{}/xmlrpc/object".format(_url))
    modules = ['ud_direcao']

    for _module in modules:
        dump_module_data(server, _db, uid, _password, _module)


if __name__ == "__main__":
    url, db, username, password = ['http://localhost:8009', "ud", "admin", "admin@ud&"]
    main(url, db, username, password)
