from traceback import print_tb
import test_handler

test_handler.message(f"Testing datamodel...")

try:
    test_handler.intecrate_api.datamodel.test()
except Exception as e:
    print_tb(e.__traceback__)
    test_handler.report(str(e), "datamodel")

test_handler.testpass("datamodel")


test_handler.message(f"Testing database...")
try:
    test_handler.intecrate_api.mongo_util.test()
except Exception as e:
    print_tb(e.__traceback__)
    test_handler.report(str(e), "database")


test_handler.message(f"Testing file manager...")
try:
    test_handler.intecrate_api.file_management.test()
except Exception as e:
    print_tb(e.__traceback__)
    test_handler.report(str(e), "database")
