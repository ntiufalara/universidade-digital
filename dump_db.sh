#!/usr/bin/env bash

_now=$(date +"%Y%m%d")
filename="../db_backup/$_now.backup"

docker-compose exec db pg_dump -v -Uodoo -wodoo -dud -f $filename