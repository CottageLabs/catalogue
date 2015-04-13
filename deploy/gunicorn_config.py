import multiprocessing

bind = "127.0.0.1:5191"
workers = multiprocessing.cpu_count() * 2 + 1
proc_name = 'catalogue'
max_requests = 1000
