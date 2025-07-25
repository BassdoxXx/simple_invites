# Gunicorn configuration file for production

# Server socket
bind = "0.0.0.0:5000"
workers = 4  # Use 2-4 x number of cores
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Process naming
proc_name = "simple_invites"
default_proc_name = "wsgi:application"

# Logging
loglevel = "debug"  # Change to 'info' after debugging
errorlog = "-"
accesslog = "-"
access_log_format = '%({X-Forwarded-For}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Server mechanics
daemon = False
raw_env = []
user = None
group = None

# Debug
reload = False
reload_extra_files = []
