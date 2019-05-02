#!/usr/bin/env bash

/src/odoo-bin -u all -d ud -r odoo -w odoo --db_host=127.0.0.1 --logfile=/src/access.log --logrotate
