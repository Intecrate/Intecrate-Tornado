#!/usr/bin/python
"""
Find jobs running in active/ and terminate them.
"""

from __future__ import annotations
import subprocess
import time
import os
import shutil
import sys


def parse_pid(string) -> int:
    out_str = ""

    for c in string:
        if c == " ":
            continue
        elif c.isnumeric():
            out_str += c
        else:
            break

    return int(out_str)


def get_pids(active_dir) -> list[int]:
    # List processes
    processes = subprocess.check_output("ps ax", shell=True).decode().split("\n")

    # Find processes running in ./active/
    death_row = []
    for process in processes:
        if active_dir in process:
            death_row.append(process)

    # Get PIDs for sentenced processes
    kill_ids = []
    for string in death_row:
        kill_ids.append(parse_pid(string))

    kill_ids = list(set(kill_ids))  # Remove duplicates
    return kill_ids


def kill(id) -> None:
    os.system(f"sudo kill {id}")


def main():
    # Fetch active dir
    this_dir = os.path.abspath(os.path.dirname(__file__))
    os.chdir(this_dir)

    # Kill processes
    to_kill = get_pids(this_dir)
    kill_list = to_kill
    for id in to_kill:
        kill(id)
        to_kill = get_pids(this_dir)

    tick = 1
    maxticks = 5
    while len(to_kill) > 0 and tick < maxticks:
        time.sleep(1)

        tick += 1
        print(
            f"Attempting to kill. Attempt {tick}/{maxticks}.\n"
            f"Targeted IDs: {to_kill}"
        )

        for id in to_kill:
            kill(id)
        to_kill = get_pids(this_dir)

    if tick >= maxticks:
        print("Failed to kill server")
        exit()

    try:
        os.remove(f"{this_dir}/nohup.out")
    except FileNotFoundError:
        print("No active server")
        exit()

    if len(kill_list) == 0:
        print("No active server")
    else:
        print(f"Killed server. ids: {kill_list}")


if __name__ == "__main__":
    main()
