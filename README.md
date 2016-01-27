# ![Universidade Digital](http://ntiufalara.github.io/universidade-digital/assets/img/logo.png)

Instalação e configuração do ambiente de desenvolvimento:

Usaremos como base o sistema Linux Ubuntu 14.04 LTS (Isso não impede a configuração em outros sistemas, porém isso não será explicado aqui).

1. Instalando as dependências do projeto (Dependências do OpenERP/Odoo):

```bash
 $ sudo apt-get install graphviz ghostscript python-dateutil python-feedparser python-gdata \
          python-ldap python-libxslt1 python-lxml python-mako \
          python-openid python-psycopg2 python-pybabel python-pychart \
          python-pydot python-pyparsing python-reportlab python-simplejson \
          python-tz python-vatnumber python-vobject python-webdav \
          python-werkzeug python-xlwt python-yaml python-imaging \
          python-matplotlib python-unittest2 python-mock python-docutils \
          python-decorator python-requests python-jinja2 python-pypdf python-passlib \
          python-psutil
```

2. Instale o servidor de banco de dados PostgreSQL.

```bash
 $ sudo apt-get install postgresql
```

3. Configure o usuário para criar e apagar Bancos de dados no servidor PostgreSQL:

Acesse o usuário de manutenção de bancos de sados:

```bash
 $ sudo su postgres
```

Configure o usuário que executará o servidor Web para obter controle total no servidor: **(Por questões de segurança, você deve usar um superusuário apenas para desenvolvimento, em produção, configure um usuário com permissões de criar e alterar bancos de dados)**

```bash
 $ createuser nomedousuario -P   # Subistitua "nomedousuario" pelo seu nome de usuário
```

Execute o script para levantar o servidor de desenvolvimento na porta 8069:

```bash
 $ ./openerp-server.py # use -h para saber mais sobre esse script
```

