FROM ubuntu:16.04

RUN \
  apt-get update && \
  apt-get install -y python-pip python-dev apache2 libapache2-mod-wsgi nano && \
  apt-get install -y graphviz python-dateutil python-feedparser python-gdata \
          python-ldap python-libxslt1 python-lxml python-mako \
          python-openid python-psycopg2 python-pybabel python-pychart \
          python-pydot python-pyparsing python-reportlab python-simplejson \
          python-tz python-vatnumber python-vobject python-webdav \
          python-werkzeug python-xlwt python-yaml python-imaging \
          python-matplotlib python-unittest2 python-mock python-docutils \
          python-decorator python-requests python-jinja2 python-pypdf python-passlib \
          python-psutil

RUN apt-get install npm wget -y && npm install -g less n && n lts

# Code config
WORKDIR /src
ADD . /src

# Apache config
RUN a2dissite 000-default.conf
RUN service apache2 stop
RUN cp /src/site.conf /etc/apache2/sites-enabled/
RUN addgroup root www-data
RUN chmod 775 -R /var/www/ && chown www-data -R /var/www/
RUN chown -R -v www-data /src

# Cron config
# RUN apt-get install -y cron
# RUN echo "* * * * * /src/cron_tasks.sh" | crontab

# Entry-point
CMD ["/bin/bash", "/src/start_server.sh"]
