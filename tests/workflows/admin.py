"""
Admin Control Test
Tests admin control endpoints.

Kyle Tennison
December 2023
"""

from tests.test_handler import TestFailure, TestHandler
import requests


def admin_test(): 
    datamodel = TestHandler.cloud_manager.datamodel
    headers = {"Authorization": TestHandler.INTECRATE_ADMIN_API_KEY} # type: ignore

    #  --------------------
    # Endpoint Functionality
    #  --------------------

    # /admin/challenge/list
    r = requests.get(
        TestHandler.make_url("/admin/challenge/list"),
        headers=headers
    )
    TestHandler.raise_for_status(r)
    clist = TestHandler.try_deserialize_model(r.json(), datamodel.ChallengeList)

    if len(clist.challenges) == 0:
        raise TestFailure(f"/admin/challenge/list returned no challenges")
    
    challenge = None

    for c in clist.challenges:
        if len(c.steps) != 0:
            challenge = c
            break

    assert challenge is not None, "no challenges have any steps"
    assert challenge.id is not None, "challenge id from /admin/challenge/list is unbound"
    print("info: /admin/challenge/list passed")

    # /admin/challenge
    r = requests.post(
        TestHandler.make_url("/admin/challenge"),
        json=datamodel.ChallengeRequest(
            challengeId=challenge.id
        ).model_dump(by_alias=True),
        headers=headers
    )
    TestHandler.raise_for_status(r)
    challenge_copy = TestHandler.try_deserialize_model(r.json(), datamodel.Challenge)

    if challenge.id != challenge_copy.id:
        raise TestFailure("/admin/challenge returned foreign challenge")
    else:
        print("info: /admin/challenge passed")
    
    # /admin/challenge/create
    r = requests.post(
        TestHandler.make_url("/admin/challenge/create"),
        json=datamodel.ChallengeCreateRequest(
            title="testing challenge",
            description="generated in test",
            coverImage="None"
        ).model_dump(by_alias=True),
        headers=headers
    )
    TestHandler.raise_for_status(r)
    new_challenge = TestHandler.try_deserialize_model(r.json(), datamodel.Challenge)
    if new_challenge.id is None:
        raise TestFailure("/admin/challenge/create returned challenge with no id")
    print("info: /admin/challenge/create passed")

    # /admin/challenge/list
    r = requests.get(
        TestHandler.make_url("/admin/challenge/list"),
        headers=headers
    )
    TestHandler.raise_for_status(r)
    clist = TestHandler.try_deserialize_model(r.json(), datamodel.ChallengeList)

    match = False
    for c in clist.challenges:
        if c.id == new_challenge.id:
            match = True 
            break 
    if not match:
        raise TestFailure(f"New challenge was excluded from /admin/challenge/list")
    print(f"/admin/challenge/list passed")

    # /admin/challenge/delete
    r = requests.delete(
        TestHandler.make_url("/admin/challenge/delete"),
        json=datamodel.ChallengeRequest(challengeId=new_challenge.id).model_dump(by_alias=True),
        headers=headers
    )
    TestHandler.raise_for_status(r)
    _msg = TestHandler.try_deserialize_model(r.json(), datamodel.MessageResponse)
    r = requests.post(
        TestHandler.make_url("/admin/challenge"),
        json=datamodel.ChallengeRequest(challengeId=new_challenge.id)
        .model_dump(by_alias=True),
        headers=headers
    )
    if r.status_code != 400:
        raise TestFailure(f"Expected code 400 for fetching deleted challenge; got {r.status_code}")

    # /admin/step
    r = requests.post(
        TestHandler.make_url("/admin/step"),
        json=datamodel.StepRequest(
            stepId=challenge.steps[0]
        ).model_dump(by_alias=True),
        headers=headers
    )
    TestHandler.raise_for_status(r)
    step = TestHandler.try_deserialize_model(r.json(), datamodel.Step)
    if step.id != challenge.steps[0]:
        raise TestFailure(f"/admin/step returned foreign step")
    print("info: /admin/step passed")

    # /admin/step/list
    r = requests.post(
        TestHandler.make_url("/admin/step/list"),
        json=datamodel.ChallengeRequest(
            challengeId=challenge.id
        ).model_dump(by_alias=True),
        headers=headers
    )
    TestHandler.raise_for_status(r)
    step_list = TestHandler.try_deserialize_model(r.json(), datamodel.StepList)
    if step.id not in [s.id for s in step_list.steps]:
        raise TestFailure(f"/admin/step/list excluded a step(s)")
    print("info: /admin/step/list passed")
    