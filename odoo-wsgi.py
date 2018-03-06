# WSGI Handler sample configuration file.
#
# Change the appropriate settings below, in order to provide the parameters
# that would normally be passed in the command-line.
# (at least conf['addons_path'])
#
# For generic wsgi handlers a global application is defined.
# For uwsgi this should work:
#   $ uwsgi_python --http :9090 --pythonpath . --wsgi-file openerp-wsgi.py
#
# For gunicorn additional globals need to be defined in the Gunicorn section.
# Then the following command should run:
#   $ gunicorn odoo:service.wsgi_server.application -c openerp-wsgi.py

import odoo
from odoo.service.server import ThreadedServer

# ----------------------------------------------------------
# Common
# ----------------------------------------------------------
odoo.multi_process = True # Nah!

# Equivalent of --load command-line option
odoo.conf.server_wide_modules = ['web']
conf = odoo.tools.config

# Path to the OpenERP Addons repository (comma-separated for
# multiple locations)
conf['addons_path'] = '/src/odoo/addons/'

# Optional database config if not using local socket
conf['db_name'] = 'ud'
conf['db_host'] = 'db'
conf['db_user'] = 'odoo'
conf['db_port'] = 5432
conf['db_password'] = 'odoo'
conf['max_cron_threads'] = 2
conf['limit_time_real_cron'] = 0

# ----------------------------------------------------------
# Generic WSGI handlers application
# ----------------------------------------------------------
application = odoo.service.wsgi_server.application

odoo.service.server.load_server_wide_modules()
# Executa as tarefas agendadas
ThreadedServer(None).cron_spawn()
# ----------------------------------------------------------
# Gunicorn
# ----------------------------------------------------------
# Standard OpenERP XML-RPC port is 8069
# bind = '127.0.0.1:8069'
# pidfile = '.gunicorn.pid'
# workers = 4
# timeout = 240
# max_requests = 2000
