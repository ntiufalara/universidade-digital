#!/bin/bash
usuario=$USER
echo
echo ">>> Atualizando repositórios do Ubuntu"
echo
sudo apt update
echo
echo ">>> Instalando Dependências do OpenERP"
echo
sudo apt install -y graphviz ghostscript postgresql-client \
          python-dateutil python-feedparser python-gdata \
          python-ldap python-libxslt1 python-lxml python-mako \
          python-openid python-psycopg2 python-pybabel python-pychart \
          python-pydot python-pyparsing python-reportlab python-simplejson \
          python-tz python-vatnumber python-vobject python-webdav \
          python-werkzeug python-xlwt python-yaml python-imaging \
          python-matplotlib python-unittest2 python-mock python-docutils \
          python-decorator python-requests python-jinja2 python-pypdf python-passlib \
          python-psutil python-pip python-setuptools postgresql git
# iniciando a configuração
echo
echo ">>> Criando usuário para o banco de dados"
echo
sudo su postgres -c "createuser $usuario -s"
cd /home/$usuario
echo
echo ">>> Clonando o repositório de código do OpenERP 7"
echo
git clone https://github.com/ntiufalara/universidade-digital.git

sudo chmod 777 /home/$usuario/ud
sudo chown $usuario /home/$usuario/ud
echo
echo ">>> Executando o servidor, abra o navegador e teste o ambiente em: http://localhost:8069"
echo
/home/$usuario/oud/openerp-server.py