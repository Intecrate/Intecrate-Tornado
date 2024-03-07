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

    # ~~~~~~~~~~~~~~~~~~~~
    #    /util/whoami
    # ~~~~~~~~~~~~~~~~~~~~
    r = requests.get(
        TestHandler.make_url("/util/whoami"),
        headers={"Authorization": TestHandler.INTECRATE_TEST_USER_KEY},  # type: ignore
    )
    TestHandler.raise_for_status(r)
    user = TestHandler.try_deserialize_model(r.json(), expected_class=datamodel.User)

    print("info: /util/whoami passed")

    # ~~~~~~~~~~~~~~~~~~~~
    #     /user/signup
    # ~~~~~~~~~~~~~~~~~~~~
    r = requests.post(
        TestHandler.make_url("/user/signup"),
        json=datamodel.SignupRequest(
            name=user.name,
            email=user.email,
            password="Password123",
            birthday=user.birthday,
        ).model_dump(by_alias=True),
    )
    TestHandler.raise_for_status(r)
    resp = TestHandler.try_deserialize_model(r.json(), datamodel.SignupResponse)

    if resp.success:
        raise TestFailure(
            f"/user/signup should have status: false when duplicate email. message: {resp.message}"
        )
    # TODO: Add a way to delete users so we can test making one
    print("info: /user/signup passed")

    # ~~~~~~~~~~~~~~~~~~~~
    #     /user/login
    # ~~~~~~~~~~~~~~~~~~~~
    r = requests.post(
        TestHandler.make_url("/user/login"),
        json=datamodel.LoginRequest(
            email=user.email, password="Password123"
        ).model_dump(by_alias=True),
    )

    TestHandler.raise_for_status(r)
    resp = TestHandler.try_deserialize_model(r.json(), datamodel.LoginResponse)
    if not resp.success or resp.user is None:
        raise TestFailure(f"Could not log into {user.email}. Message: {resp.message}")
    elif resp.user.id != user.id:
        raise TestFailure(f"/login returned foreign user id")
    else:
        print("info: /login passed")

    # ~~~~~~~~~~~~~~~~~~~~
    #   /challenge/add
    # ~~~~~~~~~~~~~~~~~~~~
    CHALLENGE_ID = "65b02270f2ff740767bbe9c8"
    auth_headers = {"Authorization": user.api_key}

    r = requests.post(
        TestHandler.make_url("/challenge/add"),
        json=datamodel.ChallengeRequest(challengeId=CHALLENGE_ID).model_dump(
            by_alias=True
        ),
        headers=auth_headers,
    )
    if r.status_code != 400:
        raise TestFailure(
            "Should have gotten 400 for challenge already existing. got:", r.status_code
        )

    # ~~~~~~~~~~~~~~~~~~~~
    #      /challenge
    # ~~~~~~~~~~~~~~~~~~~~
    r = requests.post(
        TestHandler.make_url("/challenge"),
        json=datamodel.ChallengeRequest(challengeId=CHALLENGE_ID).model_dump(
            by_alias=True
        ),
        headers=auth_headers,
    )
    added_challenge = TestHandler.try_deserialize_model(r.json(), datamodel.Challenge)
    print("info: /challenge/add passed")

    # ~~~~~~~~~~~~~~~~~~~~
    #   /challenge/list
    # ~~~~~~~~~~~~~~~~~~~~
    r = requests.get(TestHandler.make_url("/challenge/list"), headers=auth_headers)
    TestHandler.raise_for_status(r)
    challenge_list = TestHandler.try_deserialize_model(
        r.json(), datamodel.ChallengeList
    )
    if added_challenge.id not in [c.id for c in challenge_list.challenges]:
        raise TestFailure("Added challenge was not reflected in list")
    print("info: /challenge/list passed")

    # ~~~~~~~~~~~~~~~~~~~~
    #      /step/list
    # ~~~~~~~~~~~~~~~~~~~~
    r = requests.post(
        TestHandler.make_url("/step/list"),
        json=datamodel.ChallengeRequest(challengeId=CHALLENGE_ID).model_dump(
            by_alias=True
        ),
        headers=auth_headers,
    )
    TestHandler.raise_for_status(r)
    step_list = TestHandler.try_deserialize_model(r.json(), datamodel.StepList)
    if len(step_list.steps) != 3:
        raise TestFailure(
            f"Expected sample challenge to have three steps, not {len(step_list.steps)}"
        )
    step = step_list.steps[0]
    print("info: /step/list passed")

    # ~~~~~~~~~~~~~~~~~~~~
    # /step/resource/list
    # ~~~~~~~~~~~~~~~~~~~~
    r = requests.post(
        TestHandler.make_url("/step/resource/list"),
        json=datamodel.StepRequest(stepId=step.id).model_dump(by_alias=True),
        headers=auth_headers,
    )
    TestHandler.raise_for_status(r)
    resource_list = TestHandler.try_deserialize_model(
        r.json(), datamodel.StepResourceList
    )
    if len(resource_list.resources) != 3:
        raise TestFailure(
            f"Expected sample challenge to have three step resources, not {len(step_list.steps)}"
        )
    resource = resource_list.resources[0]
    print("info: /step/resource/list passed")

    # ~~~~~~~~~~~~~~~~~~~~
    #    /step/resource
    # ~~~~~~~~~~~~~~~~~~~~
    r = requests.post(
        TestHandler.make_url("/step/resource"),
        json=datamodel.StepResourceRequest(
            stepId=step.id, resourceId=resource.resource_id
        ).model_dump(by_alias=True),
        headers=auth_headers,
    )
    TestHandler.raise_for_status(r)
    resp = TestHandler.try_deserialize_model(r.json(), datamodel.StepResource)
    if resp.resource_path != resource.resource_path:
        raise TestFailure("/step/resource returned foreign resource")
    print("info: /step/resource passed")

    # ~~~~~~~~~~~~~~~~~~~~
    #    /step/{step_id}/video
    # ~~~~~~~~~~~~~~~~~~~~
    r = requests.get(
        TestHandler.make_url(f"/step/{step.id}/video"),
        headers=auth_headers
    )
    TestHandler.raise_for_status(r, check_json=False)
    if "cds.intecrate.co" not in r.url:
        raise TestFailure(
            f"/step/{step.id}/video did not return cds redirect -- got {r.url}. "
            "verify that CDS is on"
            )
    
    print("info: /step/{id}/video passed")

    # ~~~~~~~~~~~~~~~~~~~~
    #    /step/{step_id}/resource/{resource_id}/content
    # ~~~~~~~~~~~~~~~~~~~~
    r = requests.get(
        TestHandler.make_url(f"/step/{step.id}/video"),
        headers=auth_headers
    )
    TestHandler.raise_for_status(r, check_json=False)
    if "cds.intecrate.co" not in r.url:
        raise TestFailure(
            f"/step/{step.id}/video did not return cds redirect -- got {r.url}. "
            "verify that CDS is on"
            )
    
    print("info: /step/{step_id}/resource/{resource_id}/content passed")

