from cloud_manager.common.tools import log
from cloud_manager import datamodel
from cloud_manager.common.base import BaseHandler, api_get, api_post
from cloud_manager.error import RequestError
from cloud_manager.file_management import FileManager


class AdminChallenge(BaseHandler):
    """
    Fetch a challenge by id
    """

    ENDPOINT = "/admin/challenge"
    EXPECTED_REQUEST = datamodel.ChallengeRequest
    EXPECTED_RESPONSE = datamodel.Challenge

    @api_post(requires_admin=True)
    async def post(self, request: datamodel.ChallengeRequest) -> datamodel.Challenge:
        challenge_id = request.challenge_id
        return await self.db.get_challenge_strict(challenge_id)


class AdminChallengeList(BaseHandler):
    """
    Lists all the available challenges
    """

    ENDPOINT = "/admin/challenge/list"
    EXPECTED_RESPONSE = datamodel.ChallengeList

    @api_get(requires_admin=True)
    async def get(self) -> datamodel.ChallengeList:
        challenges = await self.db.list_challenges()
        return datamodel.ChallengeList(challenges=challenges)


class AdminChallengeCreate(BaseHandler):
    """
    Creates a new challenge
    """

    ENDPOINT = "/admin/challenge/create"
    EXPECTED_REQUEST = datamodel.ChallengeCreateRequest
    EXPECTED_RESPONSE = datamodel.Challenge

    @api_post(requires_admin=True)
    async def post(
        self, request: datamodel.ChallengeCreateRequest
    ) -> datamodel.Challenge:
        fm = FileManager.get_instance()
        challenge = await fm.create_challenge(
            request.title, request.description, request.cover_image
        )
        return challenge


class AdminStepList(BaseHandler):
    """
    List all the steps on a challenge
    """

    ENDPOINT = "/admin/step/list"
    EXPECTED_REQUEST = datamodel.ChallengeRequest
    EXPECTED_RESPONSE = datamodel.StepList

    @api_post(requires_admin=True)
    async def post(self, request: datamodel.ChallengeRequest) -> datamodel.StepList:
        challenge = await self.db.get_challenge_strict(request.challenge_id)
        steps: list[datamodel.Step] = []
        for step_id in challenge.steps:
            step = await self.db.get_step(step_id)
            if step is None:
                log(
                    f"challenge {challenge.id} contains nonexistent step {step_id}",
                    status="error",
                )
                continue
            steps.append(step)

        return datamodel.StepList(steps=steps)


class AdminStep(BaseHandler):
    """
    Fetch a step by its id
    """

    ENDPOINT = "/admin/step"
    EXPECTED_REQUEST = datamodel.StepRequest
    EXPECTED_RESPONSE = datamodel.Step

    @api_post(requires_admin=True)
    async def post(self, request: datamodel.StepRequest) -> datamodel.Step:
        return await self.db.get_step_strict(request.step_id)


class AdminChallengeDelete(BaseHandler):
    """
    Deletes a challenge
    """

    ENDPOINT = "/admin/challenge/delete"
    EXPECTED_REQUEST = datamodel.ChallengeRequest
    EXPECTED_RESPONSE = datamodel.MessageResponse

    @api_post(requires_admin=True)
    async def delete(
        self, request: datamodel.ChallengeRequest
    ) -> datamodel.MessageResponse:
        fm = FileManager.get_instance()
        await fm.delete_challenge(request.challenge_id)

        return datamodel.MessageResponse(
            message=f"Successfully deleted challenge {request.challenge_id}"
        )


class AdminStepCreate(BaseHandler):
    """
    Creates a new step
    """

    ENDPOINT = "/admin/step/create"
    EXPECTED_REQUEST = datamodel.StepCreateRequest
    EXPECTED_RESPONSE = datamodel.Step

    @api_post(requires_admin=True)
    async def post(self, request: datamodel.StepCreateRequest) -> datamodel.Step:
        # Not currently implemented via api
        raise RequestError(message="Not Implemented through API")
