# encoding: utf-8


# Executar esta correção no shell
# > from odoo.addons.ud_biblioteca.migracao.corrige_data_inclusao import *
# > run(env)


def update(env, pubs_old):
    Publicacao = env['ud.biblioteca.publicacao']
    for p in pubs_old:
        pub = Publicacao.search([('name', '=', p['name'])])
        print u'Atualizando: {}'.format(pub['name'])
        if pub:
            pub.visualizacoes += int(p['visualizacoes'])
            pub.create_date = p['create_date']
        else:
            print(u'Publicação não cadastrada.')
        print


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
    pub_ids = server.execute(db, uid, password, 'ud.biblioteca.publicacao', 'search', [('name', '!=', False)])
    pubs = server.execute_kw(db, uid, password, 'ud.biblioteca.publicacao', 'read', [pub_ids], {
        'fields': ['name', 'visualizacoes', 'create_date']
    })
    return pubs


def run(env):
    pubs = get_pubs_old(env)
    update(env, pubs)
    env.cr.commit()
