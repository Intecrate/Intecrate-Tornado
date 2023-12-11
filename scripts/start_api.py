#!/usr/bin/python
"""
Make a copy of this repo and start the webserver from there.
"""

from __future__ import annotations
import os
import shutil
import sys
import threading
import time


def out_read(file) -> str:
    with open(file, "r") as f:
        return f.read()


def get_new(str1, str2) -> str:
    return str2[len(str1) :]


def main():
    # Check cli arguments for skip_wait flag
    skip_wait = False
    if len(sys.argv) > 1:
        assert sys.argv[1].isnumeric(), f"illegal argument {sys.argv[1]}"
        skip_wait = bool(int(sys.argv[1]))

    print("Skip wait:", skip_wait)

    # Change to this file's dir
    this_dir = os.path.abspath(os.path.dirname(__file__))
    os.chdir(this_dir)

    # Start webserver
    cmd = f"nohup {sys.executable} -u {this_dir}/launch.py &"
    print(f"\n $ {cmd}\n")
    os.system(cmd)

    # Fetch outputfile
    out_file = os.path.join(this_dir, "nohup.out")
    time.sleep(2)

    # Keep fetching until timeout or found
    tick = 0
    max_ticks = 15
    while not os.path.exists(out_file) and tick < max_ticks:
        tick += 1
        time.sleep(0.25)
        print(f"Could not find out file: {out_file}. Retrying ({tick}/{max_ticks})")
    if tick >= max_ticks:
        print(f"Could not resolve {out_file}")
        exit()

    # Display output file for 10 seconds
    def display_out():
        prev = ""

        while True:
            time.sleep(0.1)
            new = get_new(prev, out_read(out_file))

            if new == "":
                continue

            print("\n", new, end="")
            prev += new

    display_thread = threading.Thread(target=display_out, daemon=True)
    display_thread.start()
    time.sleep(1 if skip_wait else 10)
    exit()


if __name__ == "__main__":
    main()
