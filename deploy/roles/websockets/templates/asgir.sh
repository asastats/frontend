#!/bin/bash
# Rolling restart of the Daphne workers, one at a time: the others keep serving.
# Installed by the frontend deploy (roles/websockets); the deploy runs it too.
[ "$(id -u)" -eq 0 ] || exec sudo "$0" "$@"

ctl() { supervisorctl -c /etc/supervisor/supervisord.conf "$@"; }

ctl status 'asgi:*'
for n in $(seq 0 {{ (daphne_numprocs | default(4) | int) - 1 }}); do
  p="asgi:asgi$n"
  sock="{{ site_path }}/run/daphne$n.sock"
  started=$(date +%s)
  ctl restart "$p" || exit 1

  # back only when RUNNING and its socket is the new one, not the old file
  ready=0
  for i in $(seq 1 {{ daphne_restart_timeout | default(30) }}); do
    if ctl status "$p" | grep -q RUNNING && [ -S "$sock" ] \
      && [ "$(stat -c %Y "$sock")" -ge "$started" ]; then
      ready=1
      break
    fi
    sleep 1
  done

  if [ "$ready" -ne 1 ]; then
    echo "$p did not come back within {{ daphne_restart_timeout | default(30) }}s; stopping the rollout" >&2
    ctl status "$p"
    exit 1
  fi
  ctl status "$p"
done
