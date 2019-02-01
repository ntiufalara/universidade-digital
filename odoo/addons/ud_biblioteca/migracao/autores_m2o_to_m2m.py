# encoding: UTF-8


def corrige_autores(publicacoes):
    for pub in publicacoes:
        autor = pub.autor_id
        pub.autor_ids |= autor


