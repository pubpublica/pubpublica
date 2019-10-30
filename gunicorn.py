bind = "unix:/var/run/pubpublica/pubpublica.sock"
# bind = "127.0.0.1:5000"

# worker_class= "aiohttp.worker.GunicornWebWorker"
workers = 4                     # max number of workers
max_requests = 1000             # max number of requests before a worker is restarted
max_requests_jitter = 100       # jitter to add to `max_requests', so they dont all restart at the same time
timeout = 30                    # restart stuck workers after this many seconds
graceful_timeout = 30           # a worker has his many seconds to finish its work, after receiving a kill-signal

proc_name = "pubpublica"
user = "pubpublica"             # drop privileges to this user
group = "www-data"              # and this group

loglevel = "debug"
accesslog = "/var/log/pubpublica/gunicorn_access.log"
errorlog = "/var/log/pubpublica/gunicorn_errors.log"
capture_output = True           # redirect stdout/stderr to `errorlog'
