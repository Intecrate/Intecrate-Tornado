
import uuid
from cloud_manager import datamodel
from cloud_manager.common.base import BaseHandler, api_post
from cloud_manager.common.tools import hash_str, log, verify_password
from cloud_manager.error import AuthenticationError, RequestError
from cloud_manager.handlers.util import util_checkSyntax
from dateutil.parser import parse as date_parse

class Login(BaseHandler):
    """
    Verifies user login
    """

    ENDPOINT = "/user/login"
    EXPECTED_REQUEST = datamodel.LoginRequest
    EXPECTED_RESPONSE = datamodel.LoginResponse

    TEST_REQUEST = datamodel.LoginRequest(
        email="johndoe@example.com", password="Password123"
    )

    @api_post
    async def post(self, request: datamodel.LoginRequest) -> datamodel.LoginResponse:
        email = request.email
        password = request.password


        log(f"Got login from '{email}'")

        # Check if email or password is empty
        if email is None or password is None:
            raise RequestError("Email nor password cannot be none")

        # Check if email is valid.
        if "@" in email:
            name, domain = email.split("@")
            if len(name) < 3 or not "." in domain:
                raise RequestError("Invalid email")
        else:
            raise RequestError("Invalid email")


        # Check with database for user
        id = await self.db.id_by_email(email)

        log(f"Fetched id {id} from email {email}", "debug")

        if id is None:
            raise RequestError("No account registered with this email")

        user = await self.db.get_user_strict(id)

        password_hash = await self.db.get_password_hash(user.id)

        if verify_password(password, password_hash) == False:
            raise AuthenticationError(f"Invalid password for {user.id}")

        else:
            return datamodel.LoginResponse(
                success=True,
                message="",
                user=user
            )


class Signup(BaseHandler):
    """
    Verifies signup request. Creates a new user if successful.
    """

    ENDPOINT = "/user/signup"
    EXPECTED_REQUEST = datamodel.SignupRequest
    EXPECTED_RESPONSE = datamodel.SignupResponse

    TEST_REQUEST = datamodel.SignupRequest(
        name="John Doe",
        email="johndoe@example.com",
        password="Password123",
        birthday="02-01-2005",
    )

    @api_post
    async def post(self, request: datamodel.SignupRequest) -> datamodel.SignupResponse:
        name = request.name
        email = request.email
        password = request.password
        birthday_str = request.birthday



        if not util_checkSyntax.date_syntax(birthday_str):
            return datamodel.SignupResponse(
                success=False,
                message="Bad birthday syntax",
                errorCode=0,
                user=None
            )

        birthday_datetime = date_parse(birthday_str)
        birthday = birthday_datetime.isoformat()

        log(f"Got signup from {name} / {email}")

        if not util_checkSyntax.email_syntax(email):
            return datamodel.SignupResponse(
                success=False,
                message="Bad email syntax",
                errorCode=0,
                user=None
            )

        if await self.db.id_by_email(email) is not None:
            return datamodel.SignupResponse(
                success=False,
                message="Email already attached to an account",
                errorCode=0,
                user=None
            )

        log("Got valid signup request")

        # Hash Password
        password_hash = hash_str(password)

        user = await self.db.add_user(
            name=name,
            email=email,
            password_hash=password_hash,
            birthday=birthday,
            api_key=str(uuid.uuid4()),
        )

        return datamodel.SignupResponse(
            success=True,
            message="Successfully created new user",
            errorCode=0,
            user=user
        )

class GetApiKey(BaseHandler):
    """Gets the user's API key from the user id"""

    ENDPOINT = "/user/getApiKey"
    EXPECTED_REQUEST = datamodel.UserRequest
    EXPECTED_RESPONSE = datamodel.UserGetApiKeyResponse

    TEST_REQUEST = datamodel.UserRequest(userId="some_invalid_id")

    @api_post
    async def post(self, request: datamodel.UserRequest) -> datamodel.UserGetApiKeyResponse:
        await self.assert_admin()
        id = request.id
        user = await self.db.get_user_strict(id)

        return datamodel.UserGetApiKeyResponse(
            apiKey=user.api_key,
            message="Successfully found api key"
        )
