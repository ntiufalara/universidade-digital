# Dados para importação

Os dados dentro desta pasta estão prontos para serem adicionados diretamente pelo método de importação disponível na interface do sistema.

### Importar na sequência

Módulo `ud`

1. ud.campus
2. ud.polo
3. ud.setor
4. ud.curso
5. ud.bloco (É necessário entrar na tela de importação de qualquer model e trocar a url em `model=` para ud.bloco)
6. ud.pessoa

Módulo `ud_biblioteca`

Executar o `csv_dump.py` alterando a lista de módulos para `ud_biblioteca`

1. ud.biblioteca.p_chave
2. ud.biblioteca.orientador.titulacao (É necessário entrar na tela de importação de qualquer model e trocar a url em `model=` para ud.biblioteca.orientador.titulacao)
3. ud.biblioteca.orientador
4. ud.biblioteca.responsavel
5. ud.biblioteca.publicacao.autor (Substituir URL)
6. ud.biblioteca.publicacao.area (Substituir URL)
7. ud.biblioteca.publicacao.categoria_cnpq (Substituir URL)
8. ud.biblioteca.publicacao

- As publicações devem ser retiradas a partir do script `dump_publicacoes.py` para estarem no formato correto de importação.
- Os anexos devem ser exportados a partir do script `dump_anexos.py` para estarem no formato correto de importação.
