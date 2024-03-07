"""
Tests datamodel, database, and file management without starting the server

Kyle Tennison
November 2023
"""

from traceback import print_tb
from test_handler import TestHandler

TestHandler.message(f"Testing datamodel...")

try:
    TestHandler.cloud_manager.datamodel.test()
except Exception as e:
    print_tb(e.__traceback__)
    TestHandler.report(str(e), "datamodel")

TestHandler.testpass("datamodel")


TestHandler.message(f"Testing database...")
try:
    TestHandler.cloud_manager.mongo_util.test()
except Exception as e:
    print_tb(e.__traceback__)
    TestHandler.report(str(e), "database")


TestHandler.message(f"Testing file manager...")
try:
    TestHandler.cloud_manager.file_management.test()
except Exception as e:
    print_tb(e.__traceback__)
    TestHandler.report(str(e), "database")
