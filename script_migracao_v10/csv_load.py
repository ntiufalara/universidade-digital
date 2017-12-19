# encoding: UTF-8
import os
import sys
import xmlrpclib
import csv


def open_csv(name, as_list=False):
    data = []
    with open(name, 'r') as f:
        reader = csv.reader(f) if as_list else csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data


def data_adapter(data, field_map_filename):
    field_map = open_csv(field_map_filename, as_list=True)
    for d in data:
        for field_names in field_map:
            if field_names[1] == 'remove':
                del d[field_names[0]]
            else:
                d[field_names[1]] = d.pop(field_names[0])


def load_module_data(_server, _db, _uid, _password, filename, field_map_filename=None):
    dados = open_csv(filename)
    if field_map_filename:
        data_adapter(dados, field_map_filename)
    print dados


# https://www.odoo.com/documentation/8.0/api_integration.html
# https://doc.odoo.com/6.1/developer/12_api/
# https://doc.odoo.com/6.1/developer/12_api/#python
def main(_url, _db, _username, _password):
    auth = xmlrpclib.ServerProxy("{}/xmlrpc/common".format(_url))
    uid = auth.login(_db, _username, _password)

    server = xmlrpclib.ServerProxy("{}/xmlrpc/object".format(_url))

    for f in os.listdir("."):
        if f.endswith(".csv"):
            load_module_data(server, _db, uid, _password, f)
    # load_module_data(server, _db, uid, _password, 'ud.campus.csv', 'ud.campus_map.csv')


if __name__ == "__main__":
    csv.field_size_limit(sys.maxsize)
    url, db, username, password = ['http://localhost:8069', "ud_v2", "admin", "admin@ud&"]
    main(url, db, username, password)
