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
#   $ gunicorn openerp:service.wsgi_server.application -c openerp-wsgi.py

import openerp
from openerp.service import cron

#----------------------------------------------------------
# Common
#----------------------------------------------------------
openerp.multi_process = True # Nah!

# Equivalent of --load command-line option
openerp.conf.server_wide_modules = ['web']
conf = openerp.tools.config
cron.start_service()
# Path to the OpenERP Addons repository (comma-separated for
# multiple locations)

conf['addons_path'] = '/src/openerp/addons/'

# Optional database config if not using local socket
conf['db_name'] = 'ud'
conf['db_host'] = 'db'
conf['db_user'] = 'odoo'
conf['db_port'] = 5432
conf['db_password'] = 'odoo'

#----------------------------------------------------------
# Generic WSGI handlers application
#----------------------------------------------------------
application = openerp.service.wsgi_server.application

#----------------------------------------------------------
# Gunicorn
#----------------------------------------------------------
# Standard OpenERP XML-RPC port is 8069
# bind = 'ud.ara'
# pidfile = '.gunicorn.pid'
# workers = 2
# timeout = 240
# max_requests = 2000

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
