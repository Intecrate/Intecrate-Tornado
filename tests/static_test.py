from traceback import print_tb
import test_handler

test_handler.message(f"Testing datamodel...")

try:
    test_handler.cloud_manager.datamodel.test()
except Exception as e:
    print_tb(e.__traceback__)
    test_handler.report(str(e), "datamodel")

test_handler.testpass("datamodel")


test_handler.message(f"Testing database...")
try:
    test_handler.cloud_manager.mongo_util.test()
except Exception as e:
    print_tb(e.__traceback__)
    test_handler.report(str(e), "database")


test_handler.message(f"Testing file manager...")
try:
    test_handler.cloud_manager.file_management.test()
except Exception as e:
    print_tb(e.__traceback__)
    test_handler.report(str(e), "database")
