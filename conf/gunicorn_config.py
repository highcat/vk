bind = '0.0.0.0:8080'
pidfile = '/app/var/run/gunicorn.pid'

workers = 2
worker_class = 'sync'
max_requests = 50

loglevel = 'info'
timeout = 120
