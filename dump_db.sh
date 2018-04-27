#!/usr/bin/env bash

_now=$(date +"%Y%m%d")
filename="../db_backup/$_now.backup"

docker-compose exec web pg_dump ud > $filename
