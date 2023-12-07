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
from typing import Any, Optional, Union
import json

use_https = False


class BaseHandler(tornado.web.RequestHandler):
    """
    Base handler gonna to be used instead of RequestHandler
    """

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
        """Get the API key of the request, if there is one"""
        api_key = self.request.headers.get("Authorization")
        return api_key

    async def is_admin(self) -> bool:
        """Checks if the API key belongs to an admin"""
        # "admin_key" : "cda75f74-913b-47a2-b25f-5d7b26c36e06"
        return await self.get_api_key() in s.ADMIN_API_KEYS

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

        assert isinstance(obj, datamodel.ResponseContainer) or isinstance(
            obj, datamodel.BaseModel
        ), f"illegal response type: {type(obj).__name__}"

        # Load container into datamodel object
        EXPECTED_RESPONSE = getattr(self, "EXPECTED_RESPONSE", None)

        if EXPECTED_RESPONSE is None:
            log(f"{type(self).__name__} has no EXPECTED_RESPONSE attribute", "error")
            raise Exception

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


def api_post(*args):
    """
    A decorator that allows post methods to be handled via datamodel objects.
    """

    return lambda x: inner_wrapper(x, HttpMethod.POST)

def api_get(*args):
    """
    A decorator that allows get methods to be handled via datamodel objects.
    """

    return lambda x: inner_wrapper(x, HttpMethod.POST)

def api_delete(*args):
    """
    A decorator that allows post methods to be handled via datamodel objects.
    """

    return lambda x: inner_wrapper(x, HttpMethod.POST)

def inner_wrapper(func, method: str):

    async def wrapper(self, *args, **kwargs):

        if method in (HttpMethod.POST, HttpMethod.DELETE):

            EXPECTED_REQUEST = self.EXPECTED_REQUEST
            assert issubclass(
                EXPECTED_REQUEST, datamodel.BaseModel
            ), "Expected class must be datamodel-derived"

            log("loading request_object", "debug")
            try:
                request_object = EXPECTED_REQUEST(**self.args)  # <-- The POST payload

            except ValidationError as e:
                log(f"Bad request format for {EXPECTED_REQUEST.__name__}", "warn")
                
                return

            print(f"Parsing request into {type(request_object).__name__}:")
            pprint(request_object.model_dump())

            return func(self, request_object)
        
        elif method == HttpMethod.GET:
            pass # nothing needed as of now

        else:
            raise 

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
