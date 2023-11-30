"""
Tools for running deployment tests.

August 2023
"""


import sys
import os

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)

import threading
import time
import intecrate_api


def main():
    """Runs on import"""

    # Change to api-server directory
    path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..")
    os.chdir(path)


def start_server():
    """Starts the server in a daemon-style"""

    def worker():
        intecrate_api.webserver.main()

    threading.Thread(target=worker, daemon=True).start()

    print("Waiting for server to start...")
    time.sleep(5)
    print("Assuming server has started")


def stop_server():
    exit()


def make_url(endpoint):
    return f"http://localhost:3001{endpoint}"


def message(message):
    print(f"\033[92m{message}\x1b[0m")


def warn(message):
    print(f"\033[93m {message}\033[00m")


def report(message, testname):
    print(f"\033[91m Test {testname} failed: {message}\033[0m")
    sys.stderr.write(message)
    exit(1)


def testpass(testname):
    print(f"\033[92m \n\nTEST '{testname.upper()}' PASSED \x1b[0m")


main()
