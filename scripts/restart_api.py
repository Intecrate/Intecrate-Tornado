import os
import sys

skip_wait = False

if len(sys.argv) > 1:
    assert sys.argv[1].isnumeric(), f"illegal argument {sys.argv[1]}"
    skip_wait = bool(int(sys.argv[1]))

os.chdir(os.path.abspath(os.path.dirname(__file__)))

os.system(f"{sys.executable} stop_api.py")
os.system(f"{sys.executable} start_api.py {int(skip_wait)}")
