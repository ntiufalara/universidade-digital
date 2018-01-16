#/bin/bash

# Apache
rm /var/run/apache2/* -rf
source /etc/apache2/envvars
service apache2 start
tail -f /src/access.log -f /src/error.log
