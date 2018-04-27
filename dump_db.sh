#!/usr/bin/env bash

_now=$(date +"%Y%m%d")
filename="../db_backup/$_now.backup"

docker-compose exec db pg_dump -Uodoo -wodoo -dud > $filename
