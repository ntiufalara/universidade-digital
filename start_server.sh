#/bin/bash
export PYTHONIOENCODING=utf8
/src/openerp-server.py -u all -r odoo -w odoo -d ud --db_host=db --logfile=/src/access.log
