from cloud_manager.common.tools import log
from cloud_manager import datamodel
from cloud_manager.common.base import BaseHandler, apipost
from cloud_manager.file_management import FileManager


class AdminChallenge(BaseHandler):
    """
    Fetch a challenge by id
    """

    ENDPOINT = "/admin/challenge"
    EXPECTED_REQUEST = datamodel.ChallengeRequest
    EXPECTED_RESPONSE = datamodel.Challenge

    @apipost
    async def post(self, request: datamodel.ChallengeRequest):
        challenge_id = request.challenge_id
        challenge = await self.db.get_challenge(challenge_id)
        if challenge is None:
            await self.respond(
                datamodel.GenericError(
                    message=f"No challenge {challenge_id} exists", code=0
                ), 400
            )

        else:
            await self.respond(challenge)


class AdminChallengeList(BaseHandler):
    """
    Lists all the available challenges
    """

    ENDPOINT = "/admin/challenge/list"
    EXPECTED_RESPONSE = datamodel.ChallengeList

    async def get(self):
        challenges = await self.db.list_challenges()

        await self.respond(datamodel.ChallengeList(challenges=challenges))


class AdminChallengeCreate(BaseHandler):
    """
    Creates a new challenge
    """

    ENDPOINT = "/admin/challenge/create"
    EXPECTED_REQUEST = datamodel.ChallengeCreateRequest
    EXPECTED_RESPONSE = datamodel.Challenge

    @apipost
    async def post(self, request: datamodel.ChallengeCreateRequest):
        fm = FileManager.get_instance()

        challenge = await fm.create_challenge(
            request.title, request.description, request.cover_image
        )

        await self.respond(challenge)


class AdminChallengeStepList(BaseHandler):
    """
    List all the challenges on
    """

    ENDPOINT = "/admin/challenge/step/list"
    EXPECTED_REQUEST = datamodel.ChallengeRequest
    EXPECTED_RESPONSE = datamodel.StepList

    @apipost
    async def post(self, request: datamodel.ChallengeRequest):
        challenge = await self.db.get_challenge(request.challenge_id)

        if challenge is None:
            await self.respond(
                datamodel.GenericError(
                    message=f"No challenge {request.challenge_id} exists", code=0
                ),
                400,
            )
            return

        steps: list[datamodel.Step] = []
        for step_id in challenge.steps:
            step = await self.db.get_step(step_id)
            if step is None:
                log(f"challenge {challenge.id} contains nonexistent step {step_id}")
                continue
            steps.append(step)

        await self.respond(datamodel.StepList(steps=steps))


class AdminStep(BaseHandler):
    """
    Fetch a step by its id
    """

    ENDPOINT = "/admin/step"
    EXPECTED_REQUEST = datamodel.StepRequest
    EXPECTED_RESPONSE = datamodel.Step

    @apipost
    async def post(self, request: datamodel.StepRequest):
        step = await self.db.get_step(request.step_id)

        if step is None:
            await self.respond(
                datamodel.GenericError(
                    message=f"No step {request.step_id} exists", code=0
                )
            )
        else:
            await self.respond(step)


class AdminChallengeDelete(BaseHandler):
    """
    Deletes a challenge
    """

    ENDPOINT = "/admin/challenge/delete"
    EXPECTED_REQUEST = datamodel.ChallengeRequest
    EXPECTED_RESPONSE = datamodel.MessageResponse

    @apipost
    async def delete(self, request: datamodel.ChallengeRequest):
        fm = FileManager.get_instance()
        try:
            await fm.delete_challenge(request.challenge_id)
        except Exception as e:
            await self.respond(datamodel.GenericError(message=str(e), code=0), 500)
            return

        await self.respond(
            datamodel.MessageResponse(
                message=f"Successfully deleted challenge {request.challenge_id}"
            )
        )


class AdminStepCreate(BaseHandler):
    """
    Creates a new step
    """

    ENDPOINT = "/admin/step/create"
    EXPECTED_REQUEST = datamodel.StepCreateRequest
    EXPECTED_RESPONSE = datamodel.Step

    @apipost
    async def post(self, request: datamodel.StepCreateRequest):
        # Not currently implemented via api
        await self.respond(
            datamodel.GenericError(message="Not Implemented through API", code=0)
        )
