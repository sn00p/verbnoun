#!/usr/bin/env bash

# start uswgi
#uwsgi --ini /usr/src/verbnoun/conf.ini &
uwsgi --plugin python3  --ini /usr/src/verbnoun/conf.ini &

# start nginx.
service nginx restart

tail -f /dev/null
