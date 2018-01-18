# encoding: UTF-8

import xmlrpclib


def corrige_autor(_server, _db, _uid, _password):
    pub = _server.execute(_db, _uid, _password, 'ud.biblioteca.publicacao', 'search', [])
    objs = _server.execute(_db, _uid, _password, 'ud.biblioteca.publicacao', 'read', pub)
    for obj in objs:
        id = [obj.get('id')]

        autorid = _server.execute(_db, _uid, _password, 'ud.biblioteca.publicacao.autor', 'create', {
            'name': obj.get('autor')
        })
        print obj.get('autor')
        print autorid
        _server.execute(_db, _uid, _password, 'ud.biblioteca.publicacao', 'write', id, {
            'autor_id': autorid
        })


def corrigir_tipo(_server, _db, _uid, _password):
    pub = _server.execute(_db, _uid, _password, 'ud.biblioteca.publicacao', 'search', [])
    objs = _server.execute(_db, _uid, _password, 'ud.biblioteca.publicacao', 'read', pub)
    for obj in objs:
        id = [obj.get('id')]

        tipoid = _server.execute(_db, _uid, _password, 'ud.biblioteca.publicacao.tipo', 'search', [
            ('name', '=', obj.get('tipo'))
        ])
        print obj.get('tipo')
        if obj.get('tipo') and not tipoid:
            print tipoid
            tipoid = _server.execute(_db, _uid, _password, 'ud.biblioteca.publicacao.tipo', 'create', {
                'name': obj.get('tipo')
            })
        else:
            tipoid = 1
        # print tipoid
        if type(tipoid) == list:
            tipoid = tipoid[0]
        _server.execute(_db, _uid, _password, 'ud.biblioteca.publicacao', 'write', id, {
            'tipo_id': tipoid
        })


# https://www.odoo.com/documentation/8.0/api_integration.html
# https://doc.odoo.com/6.1/developer/12_api/
# https://doc.odoo.com/6.1/developer/12_api/#python
def main(_url, _db, _username, _password):
    auth = xmlrpclib.ServerProxy("{}/xmlrpc/common".format(_url))
    uid = auth.login(_db, _username, _password)

    server = xmlrpclib.ServerProxy("{}/xmlrpc/object".format(_url))

    corrige_autor(server, _db, uid, _password)
    corrigir_tipo(server, _db, uid, _password)

    indefid = server.execute(db, uid, password, 'ud.biblioteca.orientador', 'create', {
        'name': 'indefinido'
    })

    ''' Adiciona orientador indefinido a todas as publicações sem orientador '''
    pub = server.execute(db, uid, password, 'ud.biblioteca.publicacao', 'search', [('orientador_ids', '=', False)])
    print len(pub)

    server.execute(db, uid, password, 'ud.biblioteca.publicacao', 'write', pub, {
        'orientador_ids': [(4, indefid)]
    })
    pub = server.execute(db, uid, password, 'ud.biblioteca.publicacao', 'search', [('orientador_ids', '=', False)])
    print len(pub)


if __name__ == "__main__":
    url, db, username, password = ['http://localhost:8069', "ud", "admin", "admin@ud&"]
    main(url, db, username, password)
