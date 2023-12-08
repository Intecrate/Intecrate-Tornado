"""
Tools for running deployment tests

Kyle Tennison
August 2023
"""

from __future__ import annotations
import pprint
import subprocess
import sys
import os
import threading
import time
from typing import Optional, Type

import requests

from cloud_manager import datamodel

# Add cloud_manager to sys path
parent_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)
import cloud_manager


class TestFailure(BaseException):
    ...


# def __init__(self, message: str, test_name: str):
#     TestHandler.report(message, test_name)
class TestHandler:
    cloud_manager = cloud_manager
    secrets = {}
    log_path = os.path.realpath(
        os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "server.log")
    )

    @classmethod
    def start_server(cls) -> None:
        """Starts the server daemon thread"""

        path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..")
        os.chdir(path)

        # clear server log
        with open(cls.log_path, "wb") as f:
            f.write(b"")

        ServerManager.start_server()

    @staticmethod
    def stop_server() -> None:
        """Kills the server thread by exiting the program"""
        ServerManager.stop_server()
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

    @classmethod
    def report(cls, message: str, test_name: str) -> None:
        """Reports an error to the test handler. Shuts down server and
            exits test

        Args:
            message: The message to report
            test_name: The name of the test that is being reported

        """
        # Write log
        # ServerManager.write_log(cls.log_path)
        ServerManager.stop_server()

        print(
            f"\033[91mTest {test_name} failed: {message}\033[0m\n"
            f"Log available at {cls.log_path}"
        )
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

    @classmethod
    def check_environ(cls) -> None:
        """Checks the environment variables for the necessary tokens

        Raises:
            TestFailure if not all keys are present
        """

        required_vars = [
            "INTECRATE_TEST_USER_KEY",
            "INTECRATE_ADMIN_API_KEY",
        ]

        for key, value in os.environ.items():
            if key in required_vars:
                setattr(cls, key, value)
                required_vars.remove(key)

        if len(required_vars) > 0:
            raise TestFailure(
                f"Missing environment variables: {required_vars}",
                "Environment variable check",
            )

    @classmethod
    def raise_for_status(cls, resp: requests.Response, check_json: bool = True):
        """Checks a requests response object for failure code or non-json
            schema.

        Args:
            resp: The response object to check
            check_json: Check the response for a json response

        Raises:
            TestFailure if the resp is invalid
        """
        assert isinstance(
            resp, requests.Response
        ), f"resp is not type Response; found {type(resp).__name__}"

        if check_json:
            try:
                json: dict = resp.json()
            except requests.JSONDecodeError:
                raise TestFailure(
                    f"Invalid response from {resp.url} -- not json schema:\n{resp.text}"
                )

            if len(json) == 0:
                raise TestFailure(f"Invalid response from {resp.url} -- json empty")
        try:
            resp.raise_for_status()
        except requests.HTTPError:
            raise TestFailure(
                f"Invalid response from {resp.url} -- code {resp.status_code}:\n{pprint.pformat(resp.json())}"
            )

    @classmethod
    def try_deserialize_model[T](cls, json: dict, expected_class: Type[T]) -> T:
        """Tries to deserialize a json dict into a datamodel object

        Args:
            json: The json to deserialize
            expected_class: The datamodel class to deserialize into
        """
        assert issubclass(
            expected_class, datamodel.BaseModel
        ), "expected_class must derive from pedantic base model"

        try:
            obj = expected_class(**json)
        except Exception:
            raise TestFailure(
                f"Could not serialize the following into {type(expected_class).__name__}:\n"
                f"{json}"
            )

        return obj


class ServerManager:
    server_process: Optional[subprocess.Popen[bytes]] = None

    @classmethod
    def start_server(cls):
        if cls.server_process is not None:
            print("Server is already running.")
            return

        try:
            cls.server_process = subprocess.Popen(
                [sys.executable, "scripts/launch.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            assert cls.server_process.stdout is not None
            # for line in cls.server_process.stdout:
            #     print(line.decode())
            #     if "listening on port" in line.decode():
            #         print(f"Started server with pid {cls.server_process.pid}")
            #         break
            time.sleep(1)
            return

        except Exception as e:
            print(f"Error starting server: {e}")
            os._exit(1)

    @classmethod
    def stop_server(cls):
        if cls.server_process is None:
            print("Server is not running.")
            return

        try:
            cls.server_process.terminate()
            cls.server_process.wait()
            if cls.server_process.stderr is not None:
                print(f"Server stderr:\n\n {cls.server_process.stderr.read().decode()}")
            cls.server_process = None
            print("info: server stopped")
        except Exception as e:
            print(f"Error stopping server: {e}")
            os._exit(1)

    # @classmethod
    # def write_log(cls, filepath: str):
    #     """Writes the stdout of the server to a file"""
    #     assert cls.server_process is not None, "Cannot show stdout for unopened server"
    #     assert cls.server_process.stdout is not None

    #     print("info: writing server log...")

    #     with open(filepath, 'w') as f:
    #         for line in cls.server_process.stdout:
    #             f.write(line.decode() + "\n")
    #             print('writing:', line.decode())


# Scan environment on import
TestHandler.check_environ()
