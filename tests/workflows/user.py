"""
User Utilities Test
Tests some authentication features pertaining to user accounts.

Kyle Tennison
December 2023
"""

from tests.test_handler import TestFailure, TestHandler
import requests


def user_test(): 

    datamodel = TestHandler.cloud_manager.datamodel

    # /util/whoami
    r = requests.get(
        TestHandler.make_url("/util/whoami"),
        headers={"Authorization": TestHandler.INTECRATE_TEST_USER_KEY} # type: ignore
    )

    TestHandler.raise_for_status(r)
    resp = TestHandler.try_deserialize_model(r.json(), expected_class=datamodel.UtilWhoamiResponse)
    if resp.user is None or resp.user.id is None:
        raise TestFailure(f"No user from /util/whoami. Message: {resp.message}")
    else:
        print("info: /util/whoami passed")
    user = resp.user

    # # /signup
    # r = requests.post(
    #     TestHandler.make_url("/signup"),
    #     json=datamodel.SignupRequest(
    #     # name=user.name,
    #     # email=user.email,
    #     # name="tester bot",
    #     # email="tester@tester.test",
    #     # password="Password123",
    #     # birthday=user.birthday,
    #     birthday = "02-01-2005"
    # ).model_dump(by_alias=True))

    # TestHandler.raise_for_status(r)
    # resp = TestHandler.try_deserialize_model(r.json(), datamodel.SignupResponse)

    # print(resp)
    # exit()

    if resp.user is None:
        raise TestFailure(f"/signup returned with empty user")
    if resp.user.id != user.id:
        raise TestFailure(f"/signup returned foreign user id")


    # /login
    r = requests.post(
        TestHandler.make_url("/login"),
        json = datamodel.LoginRequest(
            email=user.email,
            password="Password123"
        ).model_dump(by_alias=True)
    )

    TestHandler.raise_for_status(r)
    resp = TestHandler.try_deserialize_model(r.json(), datamodel.LoginResponse)
    if not resp.success or resp.user is None:
        raise TestFailure(f"Could not log into {user.email}. Message: {resp.message}")
    elif resp.user.id != user.id:
        raise TestFailure(f"/login returned foreign user id")
    else:
        print("info: /login passed")
    



    