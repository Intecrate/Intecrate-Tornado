from uuid import uuid4
import uuid

from cloud_manager.common.tools import extension_to_filetype, log
import cloud_manager.common.tools as tools
from cloud_manager import datamodel
from cloud_manager.common.base import BaseHandler, api_get, api_post
from cloud_manager.error import AuthenticationError, InternalError, RequestError
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

    @api_post(requires_login=True)
    async def post(self, request: datamodel.ChallengeRequest) -> datamodel.StepList:
        api_key = await self.get_api_key_strict()
        user = await self.db.user_by_key(api_key)

        # Check if user has access to challenge
        has_access = False
        for active_challenge in user.challenges:
            if active_challenge.challenge_id == request.challenge_id:
                has_access = True

        if not has_access:
            raise AuthenticationError("User does not have access to challenge")

        challenge = await self.db.get_challenge_strict(request.challenge_id)

        steps: list[datamodel.Step] = []
        for step in challenge.steps:
            s = await self.db.get_step(step)
            if s is None:
                log(
                    f"Challenge {challenge.id} references nonexistent step",
                    status="error",
                )
                continue
            steps.append(s)

        return datamodel.StepList(steps=steps)


class StepResourceList(BaseHandler):
    """
    Lists the resources attached to a step
    """

    ENDPOINT = "/step/resource/list"
    EXPECTED_REQUEST = datamodel.StepRequest
    EXPECTED_RESPONSE = datamodel.StepResourceList

    @api_post(requires_login=True)
    async def post(self, request: datamodel.StepRequest) -> datamodel.StepResourceList:
        step = await self.db.get_step_strict(request.step_id)
        api_key = await self.get_api_key_strict()
        user = await self.db.user_by_key(api_key)

        has_access = False
        for active_challenge in user.challenges:
            if active_challenge.challenge_id == step.challenge_id:
                has_access = True
                break

        if not has_access:
            raise AuthenticationError(f"User does not have access to step {step.id}")

        return datamodel.StepResourceList(resources=step.help_resources)


class StepResource(BaseHandler):
    """
    Gets information about a step's resource
    """

    ENDPOINT = "/step/resource"
    EXPECTED_REQUEST = datamodel.StepResourceRequest
    EXPECTED_RESPONSE = datamodel.StepResource

    @api_post(requires_login=True)
    async def post(
        self, request: datamodel.StepResourceRequest
    ) -> datamodel.StepResource:
        api_key = await self.get_api_key_strict()
        user = await self.db.user_by_key(api_key)
        step = await self.db.get_step_strict(request.step_id)

        matching_resource = None
        for resource in step.help_resources:
            if resource.resource_id == request.resource_id:
                matching_resource = resource

        if matching_resource is None:
            raise RequestError(
                f"Resource {request.resource_id} does not belong to step {request.step_id}"
            )

        has_access = False
        for active_challenge in user.challenges:
            if active_challenge.challenge_id == step.challenge_id:
                has_access = True
                break

        if not has_access:
            raise AuthenticationError(
                f"User does not have access to step {request.step_id}"
            )

        return matching_resource


class StepVideo(BaseHandler):
    """
    Streams the main video for a step
    """

    ENDPOINT = r"/step/(.*?)/video"
    EXPECTED_RESPONSE = datamodel.MessageResponse

    @api_get(requires_login=True, no_return=True)
    async def get(self, step_id: str):

        step = await self.db.get_step_strict(step_id)

        filetype = extension_to_filetype(step.video_path.split('.')[-1])

        if filetype is None:
            raise InternalError(
                f"Could not determine step video ({step.video_path}) filetype",
                operation="Create CDS url"
            )

        file = datamodel.File(
            file_id = str(uuid.uuid4()),
            path = step.video_path,
            filetype = filetype,
            name = step.step_name
        )

        await self.db.upload_file_model(file)

        cds_url = f"https://cds.intecrate.co/downloadFile?fileId={file.file_id}"

        print(file.model_dump_json(indent=4))

        self.redirect(cds_url)

class StepResourceContent(BaseHandler):
    """
    Streams a resource file for a step
    """

    ENDPOINT = r"/step/(.*?)/resource/(.*?)/content"
    EXPECTED_RESPONSE = datamodel.MessageResponse

    @api_get(requires_login=True, no_return=True)
    async def get(self, step_id: str, resource_id: str):

        try:
            resource = await self.db.get_step_resource(step_id, resource_id)
        except DatabaseError:
            raise RequestError(f"Step {step_id} does not exist")

        if resource is None:
            raise RequestError(f"Resource {resource_id} does not belong to step {step_id}")
            


        filetype = extension_to_filetype(resource.resource_path.split('.')[-1])

        if filetype is None:
            raise InternalError(
                f"Could not determine step video ({resource.resource_path}) filetype",
                operation="Create CDS url"
            )

        file = datamodel.File(
            file_id = str(uuid.uuid4()),
            path = resource.resource_path,
            filetype = filetype,
            name = f"Step {step_id} resource: {resource.prompt}"
        )

        await self.db.upload_file_model(file)

        cds_url = f"https://cds.intecrate.co/downloadFile?fileId={file.file_id}"

        print(file.model_dump_json(indent=4))

        self.redirect(cds_url)