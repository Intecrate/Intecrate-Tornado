from uuid import uuid4

from cloud_manager.common.tools import log
import cloud_manager.common.tools as tools
from cloud_manager import datamodel
from cloud_manager.common.base import BaseHandler, apipost
from cloud_manager.file_management import FileManager
from cloud_manager.datamodel import ResponseContainer
from cloud_manager.common.mongo_util import DatabaseError


class StepList(BaseHandler):
    """
    Lists the steps on a challenge
    """

    ENDPOINT = "/step/list"
    EXPECTED_REQUEST = datamodel.ChallengeRequest
    EXPECTED_RESPONSE = datamodel.StepList

    @apipost
    async def post(self, request: datamodel.ChallengeRequest):
        api_key = await self.get_api_key()

        if api_key is None:
            await self.respond(
                datamodel.GenericError(message="User is not logged in", code=0), 403
            )
            return

        user = await self.db.user_by_key(api_key)
        if user is None or user.id is None:
            await self.respond(
                datamodel.GenericError(message="Invalid API Key", code=0), 403
            )
            return

        # Check if user has access to challenge
        has_access = False
        for active_challenge in user.challenges:
            if active_challenge.challenge_id == request.challenge_id:
                has_access = True

        if not has_access:
            await self.respond(
                datamodel.GenericError(
                    message="User does not have access to challenge", code=0
                ),
                403,
            )
            return

        challenge = await self.db.get_challenge(request.challenge_id)
        if challenge is None or challenge.id is None:
            await self.respond(
                datamodel.GenericError(
                    message=f"Challenge {request.challenge_id} does not exist", code=0
                ),
                400,
            )
            return

        steps: list[datamodel.Step] = []
        for step in challenge.steps:
            s = await self.db.get_step(step)
            if s is None:
                log(
                    f"Challenge {challenge.id} references nonexistent step",
                    status="warn",
                )
                continue
            steps.append(s)

        await self.respond(datamodel.StepList(steps=steps))


class StepResourceList(BaseHandler):
    """
    Lists the resources attached to a step
    """

    ENDPOINT = "/step/resource/list"
    EXPECTED_REQUEST = datamodel.StepRequest
    EXPECTED_RESPONSE = datamodel.StepResourceList

    @apipost
    async def post(self, request: datamodel.StepRequest):
        step = await self.db.get_step(request.step_id)
        if step is None or step.id is None:
            await self.respond(
                datamodel.GenericError(message="Step does not exist", code=0), 400
            )
            return

        api_key = await self.get_api_key()

        if api_key is None:
            await self.respond(
                datamodel.GenericError(message="User is not logged in", code=0), 403
            )
            return

        user = await self.db.user_by_key(api_key)
        if user is None or user.id is None:
            await self.respond(
                datamodel.GenericError(message="Invalid API Key", code=0), 403
            )
            return

        has_access = False
        for active_challenge in user.challenges:
            if active_challenge.challenge_id == step.challenge_id:
                has_access = True
                break

        if not has_access:
            await self.respond(
                datamodel.GenericError(
                    message="User does not have access to step", code=0
                ),
                403,
            )
            return

        await self.respond(datamodel.StepResourceList(resources=step.help_resources))


class StepResource(BaseHandler):
    """
    Gets information about a step's resource
    """

    ENDPOINT = "/step/resource"
    EXPECTED_REQUEST = datamodel.StepResourceRequest
    EXPECTED_RESPONSE = datamodel.StepResource

    @apipost
    async def post(self, request: datamodel.StepResourceRequest):
        step = await self.db.get_step(request.step_id)
        if step is None or step.id is None:
            await self.respond(
                datamodel.GenericError(message="Step does not exist", code=0), 400
            )
            return

        matching_resource = None
        for resource in step.help_resources:
            if resource.resource_id == request.resource_id:
                matching_resource = resource

        if matching_resource is None:
            await self.respond(
                datamodel.GenericError(
                    message="Resource does not belong to step", code=0
                ),
                400,
            )
            return

        api_key = await self.get_api_key()

        if api_key is None:
            await self.respond(
                datamodel.GenericError(message="User is not logged in", code=0), 403
            )
            return

        user = await self.db.user_by_key(api_key)
        if user is None or user.id is None:
            await self.respond(
                datamodel.GenericError(message="Invalid API Key", code=0), 403
            )
            return

        has_access = False
        for active_challenge in user.challenges:
            if active_challenge.challenge_id == step.challenge_id:
                has_access = True
                break

        if not has_access:
            await self.respond(
                datamodel.GenericError(
                    message="User does not have access to resource", code=0
                ),
                403,
            )
            return

        await self.respond(matching_resource)
