# Daphne workers' status (the rolling restart is /usr/local/bin/asgir).
# Installed by the frontend deploy (roles/websockets).
alias sasgi="sudo supervisorctl -c /etc/supervisor/supervisord.conf status 'asgi:*'"
