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
                row.append(unicode(instancia[c]).encode('utf-8'))
            writer.writerow(row)


def dump_module_data(_server, _db, _uid, _password, module):
    models_ids = _server.execute(_db, _uid, _password, 'ir.model', 'search', [])
    models = _server.execute(_db, _uid, _password, 'ir.model', 'read', models_ids)
    module_models = []

    for model in models:
        if module in model.get('modules').split(','):
            module_models.append(model)

    for model in module_models:
        # print(model.get('model'))
        objs = []
        try:
            obj_ids = _server.execute(_db, _uid, _password, model.get('model'), 'search', [])
        except:
            continue
        for obj_id in obj_ids:
            obj = _server.execute(_db, _uid, _password, model.get('model'), 'read', obj_id)
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
    modules = ['ud_biblioteca', 'ud']

    for module in modules:
        dump_module_data(server, _db, uid, _password, module)


if __name__ == "__main__":
    url, db, username, password = ['http://localhost:8069', "ud", "admin", "admin@ud&"]
    main(url, db, username, password)
