#!/usr/bin/env bash

/src/odoo-bin -u all -d ud -r odoo -w odoo --db_host=db --logfile=/src/access.log --logrotate
