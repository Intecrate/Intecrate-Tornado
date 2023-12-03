"""
Intecrate API Handlers

Copyright © 2023 Intecrate. All rights reserved.
Licensing Information found at: https://intecrate.co/legal/license
"""

from __future__ import annotations
from cloud_manager.common.tools import log, verify_password, hash_str
from cloud_manager.common.base import BaseHandler, apipost
from cloud_manager.datamodel import ResponseContainer
import cloud_manager.datamodel as datamodel
import cloud_manager.common.settings as s
from cloud_manager.common.mongo_util import DatabaseError
from cloud_manager.handlers.admin import *

from dateutil.parser import parse as date_parse
import uuid
import re
import bson.errors


class home(BaseHandler):
    """
    Home page that a user will find if they navigate to api.intecrate.co
    """

    ENDPOINT = "/"

    async def get(self):
        self.set_status(200)
        self.write(
            '<h1>Intecrate API</h1><a href="https://intecrate.co/">If you\'re lost, click here</a>'
        )


class benchmark(BaseHandler):
    """
    Benchmark; used for testing
    """

    ENDPOINT = "/benchmark"
    EXPECTED_REQUEST = datamodel.BenchmarkRequest
    EXPECTED_RESPONSE = datamodel.BenchmarkResponse

    TEST_REQUEST = datamodel.BenchmarkRequest(anAttribute="123")

    @apipost
    async def post(self, request):
        assert isinstance(
            request, datamodel.BenchmarkRequest
        ), f"invalid request type {type(request).__name__}"

        response = ResponseContainer()

        response.anotherAttribute = "Successful!"

        log(f"Got benchmark request. Benchmark attribute: {request.an_attribute}")

        self.set_status(200)

        await self.respond(response)


class recursiveBenchmark(BaseHandler):
    """
    Recursive benchmark; tests datamodels with datamodel children
    """

    ENDPOINT = "/recursiveBenchmark"
    EXPECTED_REQUEST = datamodel.BenchmarkRequest
    EXPECTED_RESPONSE = datamodel.RecursiveBenchmarkResponse

    TEST_REQUEST = datamodel.BenchmarkRequest(anAttribute="123")

    @apipost
    async def post(self, request):
        assert isinstance(
            request, datamodel.BenchmarkRequest
        ), f"invalid request type {type(request).__name__}"

        log(f"Got benchmark request. Benchmark attribute: {request.an_attribute}")

        response = ResponseContainer()

        response.anotherAttribute = "Successful!"
        response.child = datamodel.BenchmarkRequest()  # type: ignore

        await self.respond(response)


class login(BaseHandler):
    """
    Verifies user login
    """

    ENDPOINT = "/login"
    EXPECTED_REQUEST = datamodel.LoginRequest
    EXPECTED_RESPONSE = datamodel.LoginResponse

    TEST_REQUEST = datamodel.LoginRequest(
        email="johndoe@example.com", password="Password123"
    )

    @apipost
    async def post(self, request: datamodel.LoginRequest):
        email = request.email
        password = request.password

        response = ResponseContainer()

        log(f"Got login from '{email}' with password '{password}'")

        # Check if email or password is empty
        if email is None or password is None:
            self.write_error(400, "Email nor password can be none")
            return

        # Check if email is valid. TODO: Use actual thing for this
        if "@" in email:
            name, domain = email.split("@")
            if len(name) < 3 or not "." in domain:
                response.message = "Please enter a valid email"
                await self.respond(response)
                return
        else:
            response.message = "Please enter a valid email"
            await self.respond(response)
            return

        log("Valid past email check...", "debug")

        # Check with database for user
        id = await self.db.id_by_email(email)

        log(f"Fetched id {id} from email {email}", "debug")

        if id is None:
            response.message = "No account registered with this email"
            await self.respond(response)
            return

        user = await self.db.get_user(id)

        if user is None:
            response.message = "User does not exist"
            await self.respond(response)
            return

        password_hash = await self.db.get_password_hash(user.id)

        if verify_password(password, password_hash) == False:
            log(f"Invalid password to login {user.id}")
            response.message = "Incorrect password"
            await self.respond(response)
            return

        else:
            # Log user in
            response.success = True
            response.message = ""

            response.user = datamodel.User(
                id=user.id,
                name=user.name,
                birthday=user.birthday,
                email=user.email,
                apiKey=user.api_key,
                challenges=[],
            )

            await self.respond(response)


class signup(BaseHandler):
    """
    Verifies signup request. Creates a new user if successful.
    """

    ENDPOINT = "/signup"
    EXPECTED_REQUEST = datamodel.SignupRequest
    EXPECTED_RESPONSE = datamodel.SignupResponse

    TEST_REQUEST = datamodel.SignupRequest(
        name="John Doe",
        email="johndoe@example.com",
        password="Password123",
        birthday="02-01-2005",
    )

    @apipost
    async def post(self, request):
        name = request.name
        email = request.email
        password = request.password
        birthday_str = request.birthday

        response = ResponseContainer()

        if not util_checkSyntax.date_syntax(birthday_str):
            response.success = False
            response.message = "Bad birthday syntax"
            response.errorCode = 300
            await self.respond(response)
            return

        birthday_datetime = date_parse(birthday_str)
        birthday = birthday_datetime.isoformat()

        log(f"Got signup from {name} / {email}")

        if not util_checkSyntax.email_syntax(email):
            response.success = False
            response.message = "Bad email syntax"
            response.errorCode = 200
            await self.respond(response)
            return
        else:
            log("Good email syntax")

        if await self.db.id_by_email(email) is not None:
            response.success = False
            response.message = "Email already attached to an account"
            response.errorCode = 100
            log("Could not sign up user that already exists")
            await self.respond(response)
            return

        log("Got valid signup request")

        # Hash Password
        password_hash = hash_str(password)

        res = await self.db.add_user(
            name=name,
            email=email,
            password_hash=password_hash,
            birthday=birthday,
            api_key=str(uuid.uuid4()),
        )

        # Convert UserWithPass to User

        user_dict = res.model_dump(by_alias=True)  # type: ignore
        user = datamodel.User(**user_dict)

        if res:
            # Login to new user
            # log("Setting signed cookie")
            # self.set_signed_cookie("user", self.db.id_by_email(email))

            response.success = True
            response.errorCode = 0
            response.user = user
            await self.respond(response)

        else:
            self.write_error(500, "Failed to create new user")


class checkAuth(BaseHandler):
    """
    NGINX auth_request endpoint. Evaluates if a user should be able to access
    the private dir.
    """

    ENDPOINT = "/checkAuth"

    TEST_IGNORE = True

    async def get(self):
        log("Got checkAuth request")

        api_key = await self.get_api_key()

        if api_key is None:
            log("No API key set; rejecting request")
            self.set_status(403)
            return

        log("API key is not unbound, checking self.db for match...")

        user = await self.db.user_by_key(api_key)

        if user is None:
            log(f"API Key {api_key} is not attached to any use", "warn")
            self.set_status(403)

        else:
            log(f"Authenticating private request to user {user.id}")
            self.set_status(200)


# class challenge(BaseHandler):
#     """
#     Gets a challenge object by its id
#     """

#     ENDPOINT = "/challenge"
#     EXPECTED_REQUEST = datamodel.ChallengeRequest
#     EXPECTED_RESPONSE = datamodel.Challenge

#     TEST_REQUEST = datamodel.ChallengeRequest(id="64dbb9f7dffb45f55a2e10e1")

#     @apipost
#     async def post(self, request):
#         response = ResponseContainer()

#         id = request.id
#         challenge = await self.db.get_challenge(id)

#         if challenge is None:
#             self.write_error(400, "bad challenge id")
#             return

#         # Dump into response type
#         for k, v in challenge.model_dump(by_alias=True).items():  # type: ignore
#             setattr(response, k, v)

#         await self.respond(response)


# class challenge_step(BaseHandler):
#     """
#     Gets a challenge step object by its id
#     """

#     ENDPOINT = "/challenge/step"
#     EXPECTED_REQUEST = datamodel.StepRequest
#     EXPECTED_RESPONSE = datamodel.Step

#     TEST_REQUEST = datamodel.ChallengeStepRequest(stepId="64dbbadddffb45f55a2e10e2")

#     @apipost
#     async def post(self, request):
#         response = ResponseContainer()

#         step_id = request.step_id
#         challenge_step = await self.db.get_step(step_id)

#         if challenge_step is None:
#             self.write_error(400, "bad challenge step id")
#             return

#         # Dump into response type
#         for k, v in challenge_step.model_dump(by_alias=True).items():  # type: ignore
#             setattr(response, k, v)

#         print("response is:")
#         print(response.as_dict())

#         await self.respond(response)


class util_whoami(BaseHandler):
    """
    Gets the current user by their api key
    """

    ENDPOINT = "/util/whoami"
    EXPECTED_RESPONSE = datamodel.UtilWhoamiResponse

    async def get(self):
        response = ResponseContainer()

        try:
            api_key = await self.get_api_key()
        except DatabaseError as e:
            response.message = f"Database error: {str(e)}"
            await self.respond(response)
            return

        if api_key is None:
            response.message = "No API Key"
            await self.respond(response)
            return

        user = await self.db.user_by_key(api_key)

        if user is None:
            response.message = f"Illegal API Key {api_key}"
            await self.respond(response)
            return

        response.user = user
        response.message = "OK"

        await self.respond(response)


class util_checkSyntax(BaseHandler):
    """
    Utility to check different syntaxes
    """

    ENDPOINT = "/util/checkSyntax"
    EXPECTED_REQUEST = datamodel.UtilCheckSyntaxRequest
    EXPECTED_RESPONSE = datamodel.UtilCheckSyntaxResponse

    TEST_REQUEST = datamodel.UtilCheckSyntaxRequest(
        structure="date", content="02-01-2005"
    )

    @apipost
    async def post(self, request):
        structure = request.structure
        content = request.content

        # Find handler for the given syntax
        handler_map = {
            "date": self.date_syntax,
            "email": self.email_syntax,
        }

        handler = handler_map.get(structure, None)
        if handler is None:
            self.write_error(
                400, f"Invalid handler call. No structure {structure} exists."
            )
            return

        response = ResponseContainer()

        status = handler(content)
        if status == True:
            response.validSyntax = True
        else:
            response.validSyntax = False

        await self.respond(response)

    @staticmethod
    def date_syntax(content: str) -> bool:
        try:
            date = date_parse(content)
        except Exception as e:
            log(f"Failed to parse {content} because: {e}")
            return False

        if 2023 - date.year > 112:
            log(f"Year out of range in {content}")
            return False

        return True

    @staticmethod
    def email_syntax(content: str) -> bool:
        regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"

        if re.fullmatch(regex, content):
            return True

        else:
            return False


class user_getApiKey(BaseHandler):
    """Gets the user's API key from the user id"""

    ENDPOINT = "/user/getApiKey"
    EXPECTED_REQUEST = datamodel.UserRequest
    EXPECTED_RESPONSE = datamodel.UserGetApiKeyResponse

    TEST_REQUEST = datamodel.UserRequest(userId="some_invalid_id")

    @apipost
    async def post(self, request):
        id = request.id

        response = ResponseContainer()

        if not isinstance(id, str):
            log("User id is not a string:", id)
            self.write_error(400, "no user id provided, or incorrect type")
            return

        if not self.is_admin():
            log("Non admin users cannot get api Keys")
            self.set_status(403)
            response.message = "insufficient permission"
            await self.respond(response)
            return
        else:
            log("Admin user requesting api key")

        try:
            user = await self.db.get_user(id)
        except bson.errors.InvalidId:
            response.message = "Invalid user id"
            await self.respond(response)
            return

        if user is None:
            response.message = "User does not exist"
            await self.respond(response)
            return

        key = user.api_key

        if key is None:
            response.message = "User does not have an API key"
            await self.respond(response)
            return

        response.apiKey = key
        await self.respond(response)


def get_map() -> list[tuple]:
    """
    Gets a map of routes to handlers
    """
    classes = {name: obj for name, obj in globals().items() if isinstance(obj, type)}

    routes = []
    for name, obj in classes.items():
        if issubclass(obj, BaseHandler) and not (obj is BaseHandler):
            if not hasattr(obj, "ENDPOINT"):
                raise RuntimeError(f"Class {name} has no ENDPOINT attribute")

            endpoint = obj.ENDPOINT  # type: ignore

            routes.append((endpoint, obj))

    return routes
