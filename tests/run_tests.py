from traceback import print_tb
from typing import Callable
from tests.test_handler import TestFailure, TestHandler

from tests.workflows.user import user_test
from tests.workflows.admin import admin_test

TestHandler.start_server()

TESTS: dict[str, Callable] = {
    "User Management" : user_test,
    "Admin Control" : admin_test
}


def run():

    for test_name, test in TESTS.items():
        TestHandler.message(f"Starting test {test_name}")

        try:
            test()
        except TestFailure as e:
            TestHandler.report(str(e), test_name)
        except Exception as e:
            print_tb(e.__traceback__)
            TestHandler.report(f"Unhandled exception -- {str(e)}", test_name)
        else:
            TestHandler.testpass(test_name, no_shutdown=True)

    TestHandler.message("All tests passed 🎉")