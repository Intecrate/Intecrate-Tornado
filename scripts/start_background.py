import os
from subprocess import PIPE, Popen
import sys
import time

this_dir = os.path.dirname(__file__)
launch_script = os.path.join(this_dir, "launch.py")

process = Popen([sys.executable, launch_script], stderr=PIPE, stdout=PIPE)

print(f"Opened process on pid {process.pid}")

WAIT_TIME = 10

# Poll for a few seconds to see if there's any errors
for i in range(0, WAIT_TIME * 10, 1):
    if process.stderr.readable() and process.stderr:
        error = process.stderr.read().decode()
        if error.strip() == "":
            print("false alarm")
            continue
        print("\nGot error:")
        print(error)
        process.kill()
        exit()
    else:
        print("not readable")
    time.sleep(0.1)
