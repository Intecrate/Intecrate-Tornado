from cloud_manager import datamodel
from cloud_manager.common.base import BaseHandler, api_get, api_post
from cloud_manager.common.mongo_util import DatabaseError
from cloud_manager.error import AuthenticationError, RequestError


class Challenge(BaseHandler):
    """
    Fetches a challenge in a user's account
    """

    ENDPOINT = "/challenge"
    EXPECTED_REQUEST = datamodel.ChallengeRequest
    EXPECTED_RESPONSE = datamodel.Challenge

    @api_post(requires_login=True)
    async def post(self, request: datamodel.ChallengeRequest) -> datamodel.Challenge:
        api_key = await self.get_api_key_strict()
        user = await self.db.user_by_key(api_key)

        # Check if user already has challenge
        for active_challenge in user.challenges:
            if active_challenge.challenge_id == request.challenge_id:
                return await self.db.get_challenge_strict(active_challenge.challenge_id)

        raise AuthenticationError(f"User does not have access to challenge")


class ChallengeAdd(BaseHandler):
    """
    Adds a challenge to a user's account
    """

    ENDPOINT = "/challenge/add"
    EXPECTED_REQUEST = datamodel.ChallengeRequest
    EXPECTED_RESPONSE = datamodel.Challenge

    @api_post(requires_login=True)
    async def post(self, request: datamodel.ChallengeRequest) -> datamodel.Challenge:
        api_key = await self.get_api_key_strict()
        user = await self.db.user_by_key(api_key)

        # Check if user already has challenge
        for active_challenge in user.challenges:
            if active_challenge.challenge_id == request.challenge_id:
                raise RequestError(message="Challenge already added")

        challenge = await self.db.get_challenge_strict(request.challenge_id)

        # Add challenge to user
        await self.db.attach_challenge(user.id, challenge.id)

        return challenge


class ChallengeList(BaseHandler):
    """
    Lists the challenges that a user has access to
    """

    ENDPOINT = "/challenge/list"
    EXPECTED_RESPONSE = datamodel.ChallengeList

    @api_get(requires_login=True)
    async def get(self) -> datamodel.ChallengeList:
        api_key = await self.get_api_key_strict()
        user = await self.db.user_by_key(api_key)

        return datamodel.ChallengeList(
            challenges=[
                await self.db.get_challenge_strict(c.challenge_id)
                for c in user.challenges
            ]
        )
