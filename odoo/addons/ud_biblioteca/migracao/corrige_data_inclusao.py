# encoding: utf-8


def update_date(pubs_old):
    pass


def get_pubs_old(env):
    print(u'Baixando publicações do Openerp 7')
    import xmlrpclib
    # Conectando ao servidor externo
    server_oe7 = env['ud.server.openerp7'].search([('db', '=', 'ud')])
    url, db, username, password = server_oe7.url, server_oe7.db, server_oe7.username, server_oe7.password
    try:
        auth = xmlrpclib.ServerProxy("{}/xmlrpc/common".format(url))
        uid = auth.login(db, username, password)
    except:
        # Se não conectar, saia da função
        print(u'A conexão com o servidor Openerp7 não foi bem sucedida')
        return
    server = xmlrpclib.ServerProxy("{}/xmlrpc/object".format(url))
    # busca as publicações
    pub_ids = server.execute(db, uid, password, 'ud.biblioteca.publicacao', 'search', [])
    pubs = server.execute_kw(db, uid, password, 'ud.biblioteca.publicacao', 'read', [pub_ids])
    return pubs


