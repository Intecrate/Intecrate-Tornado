"""
Intecrate API Base

Copyright © 2023 Intecrate. All rights reserved.
Licensing Information found at: https://intecrate.co/legal/license
"""

from __future__ import annotations
import functools
from pprint import pprint
from pydantic import ValidationError
import tornado.web
import tornado.httpserver
from cloud_manager.common.tools import log
import cloud_manager.datamodel as datamodel
from cloud_manager.datamodel import HttpMethod
import cloud_manager.common.settings as s
import cloud_manager.common.mongo_util as mongo_util
from tornado.httputil import parse_multipart_form_data

import os
from typing import Any, Awaitable, Callable, Optional, Union
import json

from cloud_manager.error import (
    AuthenticationError,
    CloudManagerError,
    InternalError,
    RequestError,
)

use_https = False


class BaseHandler(tornado.web.RequestHandler):
    """
    Base handler gonna to be used instead of RequestHandler
    """

    EXPECTED_REQUEST = None
    EXPECTED_RESPONSE = None

    async def prepare(self) -> None:
        """Runs at the beginning of each request handle"""
        log(
            f"--- Got API request ---\n"
            f"\t  - protocol: {self.request.protocol}\n"
            f"\t  - host: {self.request.host}\n"
            f"\t  - path: {self.request.path}\n"
            f"\t  - method: {self.request.method}\n"
            f"\t  - admin: {await self.is_admin()}\n"
            f"\t  - api key: {await self.get_api_key()}\n"
            f"\t  - body: {self.request.body}"
            "\n"
        )

        if "Content-Type" in self.request.headers:
            content_type = self.request.headers["Content-Type"]
            print(f"Got request with Content-Type: {content_type}")
            if content_type == "application/json":
                print("loading as json")
                self.args = json.loads(self.request.body)
                print(f"Loaded to {self.args}")

    async def get_api_key(self) -> Optional[str]:
        """Get the API key of the request, if there is one

        Returns:
            The api key, or None if none exists
        """
        api_key = self.request.headers.get("Authorization")
        return api_key

    async def get_api_key_strict(self) -> str:
        """Gets the API key of the request. Raises exception if none exists

        Returns:
            The api key

        Raises:
            AuthenticationError if no key exists
        """
        key = await self.get_api_key()
        if key is not None:
            return key
        else:
            raise AuthenticationError("This endpoint requires an api key")

    async def is_admin(self) -> bool:
        """Checks if the API key belongs to an admin"""
        # "admin_key" : "cda75f74-913b-47a2-b25f-5d7b26c36e06"
        return await self.get_api_key() in s.ADMIN_API_KEYS

    async def assert_admin(self) -> str:
        """Asserts that the user is an admin. Raises an error if they are not

        Returns:
            The api key of the admin user

        Raises:
            AuthenticationError if the user is not admin"""

        if not await self.is_admin():
            raise AuthenticationError("User is not an admin")
        else:
            key = await self.get_api_key()
            if key is None:
                raise InternalError(
                    message="is_admin returned true, but key is empty",
                    operation="assert admin",
                )
            else:
                return key

    def write_error(self, status_code: int, message: str = "None", **kwargs) -> None:
        """Writes error with status"""
        log(f"API Raised Error {status_code}: {message}", "error")
        super().write_error(status_code, **kwargs)

    def write(self, chunk) -> None:
        """Writes a chunk of information"""
        log(f"(Final) Writing: {chunk}")
        super().write(chunk)

    async def get_current_user(self) -> Optional[bytes]:
        """Gets the current user's cookie"""
        log("use of deprecated method 'get_current_user'", "warn")
        return self.get_signed_cookie("user")

    async def options(self, *args) -> None:
        """Respond to the preflight OPTIONS request with a 200 status code"""
        self.set_status(200)
        self.finish()

    def set_default_headers(self):
        """Sets default headers to allow cross-origin access"""
        self.set_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.set_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.set_header("Access-Control-Allow-Origin", "*")

    async def respond(
        self,
        obj: Union[datamodel.ResponseContainer, datamodel.BaseModel],
        status_code: Optional[int] = None,
    ):
        """Writes a response using datamodel"""

        if not isinstance(obj, datamodel.BaseModel):
            log(f"Obj {obj} is not a datamodel object")
            raise Exception(f"Obj {obj} is not a datamodel object")

        # Load container into datamodel object
        EXPECTED_RESPONSE = getattr(self, "EXPECTED_RESPONSE", None)

        if EXPECTED_RESPONSE is None:
            log(f"{type(self).__name__} has no EXPECTED_RESPONSE attribute", "error")
            raise Exception(f"{type(self).__name__} has no EXPECTED_RESPONSE attribute")
        
        if EXPECTED_RESPONSE is datamodel.Skip:
            log(f"{type(self).__name__} is skipping response", "warn")
            return

        if isinstance(obj, datamodel.ResponseContainer):
            model = EXPECTED_RESPONSE(**obj.as_dict())
        else:
            model = obj

        serialized = model.model_dump(by_alias=True)

        assert isinstance(serialized, dict), f"object failed to serialize: {serialized}"

        if status_code is not None:
            self.set_status(status_code)

        self.write(model.model_dump(by_alias=True))

    async def post(self, *args, **kwargs):
        super().post()

    @property
    def db(self) -> mongo_util.Database:
        return mongo_util.Database.get_instance(testmode=self.settings["testmode"])


def api_post(requires_admin: bool = False, requires_login: bool = False):
    """
    A decorator that allows post methods to be handled via datamodel objects.
    """

    return lambda x: inner_wrapper(
        x, HttpMethod.POST, requires_admin=requires_admin, requires_login=requires_login
    )


def api_get(requires_admin: bool = False, requires_login: bool = False):
    """
    A decorator that allows get methods to be handled via datamodel objects.
    """

    return lambda x: inner_wrapper(
        x, HttpMethod.GET, requires_admin=requires_admin, requires_login=requires_login
    )


def api_delete(requires_admin: bool = False, requires_login: bool = False):
    """
    A decorator that allows post methods to be handled via datamodel objects.
    """

    return lambda x: inner_wrapper(
        x,
        HttpMethod.DELETE,
        requires_admin=requires_admin,
        requires_login=requires_login,
    )


def inner_wrapper(
    func: Callable[..., Awaitable[datamodel.BaseModel]],
    method: HttpMethod,
    requires_admin: bool,
    requires_login: bool,
):
    """An internal wrapper that handles errors in an handler

    Args:
        func: The handler function
        method:"""

    async def wrapper(self: BaseHandler, *args, **kwargs):
        request_object: Optional[BaseHandler]

        # Check authentication before processing request
        if requires_admin:
            try:
                await self.assert_admin()
            except AuthenticationError as e:
                await self.respond(e.model, e.code)
                return
        if requires_login:
            try:
                key = await self.get_api_key_strict()
                await self.db.user_by_key(key)
            except CloudManagerError as e:
                await self.respond(
                    AuthenticationError("This endpoint requires login").model
                )
                return

        # Prepare request
        log(f"Preparing request for {self.__class__.__name__}")
        if method in (HttpMethod.POST, HttpMethod.DELETE):
            # Find EXPECTED_REQUEST
            EXPECTED_REQUEST = self.EXPECTED_REQUEST
            if EXPECTED_REQUEST is None:
                await self.respond(
                    InternalError(
                        message=f"Handler class {self.__class__.__name__} has no EXPECTED_REQUEST",
                        operation="Handler wrapper",
                    ).model,
                    500,
                )
                return
            if not issubclass(EXPECTED_REQUEST, datamodel.BaseModel):
                await self.respond(
                    InternalError(
                        message=f"Handler class {self.__class__.__name__} has invalid EXPECTED_REQUEST: '{EXPECTED_REQUEST}'",
                        operation="Handler wrapper",
                    ).model,
                    500,
                )
                return

            # Deserialize request
            log("loading request_object", "debug")
            try:
                request_object = EXPECTED_REQUEST(**self.args)  # <-- The POST payload
            except ValidationError as e:
                await self.respond(
                    RequestError(
                        message=f"Bad request format for {EXPECTED_REQUEST.__name__}"
                    ).model,
                    400,
                )
                return

            print(f"Parsed request into {type(request_object).__name__}:")
            pprint(request_object.model_dump())

        elif method == HttpMethod.GET:
            request_object = None

        else:
            await self.respond(
                InternalError(
                    message=f"Unknown method {method}", operation="Handler wrapper"
                ).model
            )
            return

        # Execute handler
        log(
            f"Routing request to {self.__class__.__name__} with input: {request_object}"
        )
        try:
            if request_object is None:
                response = await func(self)
            else:
                response = await func(self, request_object)
        except CloudManagerError as e:
            await self.respond(e.model, e.code)
            return
        except Exception as e:
            await self.respond(
                InternalError(
                    f"{self.__class__.__name__} raised unhandled error",
                    operation="Handler wrapper",
                    child_error=e,
                ).model,
                500,
            )
            return

        # Validate response
        if not isinstance(response, datamodel.BaseModel):
            await self.respond(
                InternalError(
                    message=f"{func.__name__} returned illegal type {type(response).__name__}",
                    operation="Handler Wrapper",
                ).model,
                500,
            )
        else:
            await self.respond(response)

    return wrapper


def host(
    application: tornado.web.Application,
    http_port: int,
    # https_port: Optional[int] = None,
) -> None:
    # Move to this file's directory
    os.chdir(os.path.abspath(os.path.dirname(__file__)))

    # # Only use HTTPS if https_port is valid
    # global use_https
    # if https_port is not None:
    #     use_https = True

    # if http_port:
    application.listen(http_port)
    log(f"HTTP listening on port {http_port}")

    # if use_https:
    #     http_server = tornado.httpserver.HTTPServer(
    #         application,
    #         ssl_options={
    #             "certfile": os.path.join("../../certs/", "fullchain.pem"),
    #             "keyfile": os.path.join("../../certs/", "privkey.pem"),
    #         },
    #     )
    #     http_server.listen(https_port)  # type: ignore
    #     log(f"HTTPS listening on port {https_port}")

    tornado.ioloop.IOLoop.instance().start()
