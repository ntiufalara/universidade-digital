# encoding: UTF-8
import re
import xmlrpclib
import csv


modules_change = {
    'ud': {
        'replace_fields': {
            'ud_bloco_ids': 'polo_id'
        },
        'removed_fields': [
            'projeto_ids'
        ],
    }
}


def process_relations(obj):
    for field in obj:
        if type(obj[field]) is list and len(obj[field]) == 2:
            obj[field] = obj[field][1]


def dump_module_data(_server, _db, _uid, _password, _module):
    global modules_change
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
            remove_fields = []
            for field in obj:
                # Busca por campos removidos ou alterados, por módulo
                if _module in modules_change:
                    # Substitui o campo
                    if field in modules_change[_module]['replace_fields']:
                        obj[modules_change[_module]['replace_fields'][field]] = obj.pop(field)
                    # Remove campos listados como removidos
                    elif field in modules_change[_module]['removed_fields']:
                        remove_fields.append(field)
            for f in remove_fields:
                obj.pop(f)
            # process_relations(obj)
            objs.append(obj)
            print obj
            break
        if objs:
            pass
            # gera_csv(model.get('model')+'.csv', objs)


# https://www.odoo.com/documentation/8.0/api_integration.html
# https://doc.odoo.com/6.1/developer/12_api/
# https://doc.odoo.com/6.1/developer/12_api/#python
def main(_url, _db, _username, _password):
    auth = xmlrpclib.ServerProxy("{}/xmlrpc/common".format(_url))
    uid = auth.login(_db, _username, _password)

    server = xmlrpclib.ServerProxy("{}/xmlrpc/object".format(_url))
    modules = ['ud']

    for _module in modules:
        dump_module_data(server, _db, uid, _password, _module)


if __name__ == "__main__":
    url, db, username, password = ['http://localhost:8009', "ud", "admin", "admin@ud&"]
    main(url, db, username, password)
