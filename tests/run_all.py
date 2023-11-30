import os
import subprocess
import sys

TESTS = [
    "static_test.py",
    "endpoints_test.py",
    "login_test.py",
]

os.chdir(os.path.abspath(os.path.dirname(__file__)))

for test in TESTS:
    print(f"RUNNING {test}...")
    try:
        output = subprocess.run(
            ["python", test],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        print("run_all.py success: ", output.stdout)
        print(f'TEST "{test.upper()}" PASSED')

    except subprocess.CalledProcessError as e:
        print("run_all.py:", e.stdout)
        sys.stderr.write(f"\nTEST '{test.upper()}' FAILED: {e.stderr}")
        exit(1)

print("ALL TESTS PASSED")
exit(0)
