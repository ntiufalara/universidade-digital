# encoding: UTF-8
# TODO: Criar script de migração para campos de autores da publicação.


def corrige_autores(publicacoes):
    for pub in publicacoes:
        autor = pub.autor_id
        pub.autor_ids |= autor


