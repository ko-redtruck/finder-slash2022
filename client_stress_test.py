import subprocess
import sys
import threading
from bot_voting_client import connect
script_name = 'client.py'
output_prefix = 'out'
n_iter = 10

threads = [threading.Thread(target=connect) for i in range(1000)]
for thread in threads:
    thread.start()
for thread in threads:
    thread.join() # waits for thread to complete its task
