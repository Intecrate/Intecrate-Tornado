from typing import Callable
from tests.workflows.user import test as user_test
from tests.test_handler import TestFailure, TestHandler

TestHandler.start_server()

TESTS: dict[str, Callable] = {
    "User Management" : user_test
}


def run():

    for test_name, test in TESTS.items():
        TestHandler.message(f"Starting test {test_name}")

        try:
            test()
        except TestFailure as e:
            TestHandler.report(str(e), test_name)
        except Exception as e:
            TestHandler.report(f"Unhandled exception -- {str(e)}", test_name)
        else:
            TestHandler.testpass(test_name, no_shutdown=True)
