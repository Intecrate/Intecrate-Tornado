"""
Tools for running deployment tests

Kyle Tennison
August 2023
"""


import sys
import os
import threading
import time
import cloud_manager

# Add cloud_manager to sys path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)

class TestFailure(BaseException): ...
class TestHandler:

    cloud_manager = cloud_manager

    def __init__(self) -> None:
        # Change to api-server directory
        path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..")
        os.chdir(path)

    @staticmethod
    def start_server() -> None:
        """Starts the server daemon thread"""

        def worker():
            cloud_manager.webserver.main()

        threading.Thread(target=worker, daemon=True).start()

        print("Waiting for server to start...")
        time.sleep(5)
        print("Assuming server has started")

    @staticmethod
    def stop_server() -> None:
        """Kills the server thread by exiting the program"""
        exit()

    @staticmethod
    def make_url(endpoint: str) -> str:
        """Converts a endpoint into a localhost url to the test server
        
        Args:
            endpoint: The endpoint to convert into an url
        
        Returns:
            The url created by the endpoint

        """
        return f"http://localhost:3001{endpoint}"

    @staticmethod
    def message(message: str) -> None:
        """Prints a generic testing message
        
        Args:
            message: The message to print
        """
        print(f"\033[92m{message}\x1b[0m")

    @staticmethod
    def warn(message: str) -> None:
        """Prints a warning (yellow) message
        
        Args:
            message: The warning to print
        """
        print(f"\033[93m {message}\033[00m")

    @staticmethod
    def report(message: str, test_name: str) -> None:
        """Reports an error to the test handler. Shuts down server and
            exits test

        Args:
            message: The message to report
            test_name: The name of the test that is being reported
        
        """
        print(f"\033[91m Test {test_name} failed: {message}\033[0m")
        sys.stderr.write(message)
        exit(1)

    @staticmethod
    def testpass(test_name: str, no_shutdown: bool = False) -> None:
        """Signals that a test has passed. Shuts down server and
            exits test.
        
        Args:
            test_name: The name of the test that passed
            no_shutdown: Prevent the server from shutting down and
                the test from exiting
        """
        print(f"\033[92m \n\nTEST '{test_name.upper()}' PASSED \x1b[0m")

        if not no_shutdown:
            exit(0)

    @staticmethod
    def check_environ() -> None:
        """Checks the environment variables for the necessary tokens
        
        Raises:
            TestFailure if not all keys are present
        """

        required_vars = [
            "INTECRATE_TEST_USER_KEY"
        ]

        for key in os.environ.keys():
            if key in required_vars:
                required_vars.remove(key)
        
        if len(required_vars) > 0:
            raise TestFailure(f"Missing keys: {required_vars}")

        
# Scan environment on import
TestHandler.check_environ()