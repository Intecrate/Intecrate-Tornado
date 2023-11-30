from intecrate_api import datamodel
from intecrate_api.common.base import BaseHandler, apipost
from intecrate_api.common.mongo_util import DatabaseError


class ChallengeAdd(BaseHandler):
    """
    Adds a challenge to a user's account
    """

    ENDPOINT = "/challenge/add"
    EXPECTED_REQUEST = datamodel.ChallengeRequest
    EXPECTED_RESPONSE = datamodel.Challenge

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

        # Check if user already has challenge
        for active_challenge in user.challenges:
            if active_challenge.challenge_id == request.challenge_id:
                await self.respond(
                    datamodel.GenericError(message="Challenge already added", code=0),
                    400,
                )

        challenge = await self.db.get_challenge(request.challenge_id)
        if challenge is None or challenge.id is None:
            await self.respond(
                datamodel.GenericError(
                    message=f"Challenge {request.challenge_id} does not exist", code=0
                ),
                400,
            )
            return

        # Add challenge to user
        try:
            await self.db.attach_challenge(user.id, challenge.id)
        except DatabaseError as e:
            await self.respond(
                datamodel.GenericError(
                    message=f"Failed to attach challenge {challenge.id}: {str(e)}",
                    code=0,
                ),
                500,
            )
            return

        await self.respond(challenge)


class ChallengeList(BaseHandler):
    """
    Lists the challenges that a user has access to
    """

    ENDPOINT = "/challenge/list"
    EXPECTED_RESPONSE = datamodel.ChallengeList

    async def get(self):
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
