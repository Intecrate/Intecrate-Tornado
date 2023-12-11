"""
Tests all GET and POST endpoints.

August 2023
"""

import sys
import os
import requests
import test_handler
import time

api = test_handler.cloud_manager.api
api_map = api.get_map()

test_handler.start_server()

for endpoint, handler in api_map:
    test_handler.message(f"Testing {handler.__name__}...")

    if not hasattr(handler, "EXPECTED_REQUEST") or not hasattr(handler, "TEST_REQUEST"):
        if hasattr(handler, "TEST_IGNORE"):
            test_handler.message(f"Skipping {handler.__name__}")
            continue

        # Check if POST is implemented
        url = test_handler.make_url(endpoint)
        response = requests.post(url, json={})

        if response.status_code != 405:
            test_handler.report(
                f"POST handler '{handler.__name__}' is missing EXPECTED_REQUEST or TEST_REQUEST",
                "endpoints test",
            )

        # Test if GET is working
        response = requests.get(url)
        if response.status_code != 200:
            test_handler.report(
                f"GET handler '{handler.__name__}' failed with code {response.status_code}",
                "endpoints test",
            )

    else:
        payload = handler.EXPECTED_REQUEST().model_dump(by_alias=True)
        request = handler.TEST_REQUEST
        url = test_handler.make_url(endpoint)
        response = requests.post(url, json=request.model_dump(by_alias=True))

        if response.status_code != 200:
            test_handler.report(
                f"POST handler '{handler.__name__}' returned "
                f"with code {response.status_code}",
                "endpoints test",
            )

        if response.status_code in (500, 400):
            test_handler.report(
                f"POST handler '{handler.__name__}' failed with code {response.status_code}\n",
                "endpoints test",
            )


test_handler.testpass("All endpoints passed")
