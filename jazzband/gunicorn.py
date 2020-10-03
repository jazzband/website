import multiprocessing
import os

worker_tmp_dir = "/dev/shm"

workers = multiprocessing.cpu_count() * 2 + 1
threads = 4

timeout = 60

accesslog = errorlog = "-"
capture_output = True

max_requests = 5000

port = os.environ.get("PORT", 5000)
bind = f"0.0.0.0:{port}"
