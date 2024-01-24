"""
Intecrate API Datamodel

Copyright © 2023 Intecrate. All rights reserved.
Licensing Information found at: https://intecrate.co/legal/license
"""

from __future__ import annotations
from enum import Enum
from typing import Optional, Union, Any, List

from typing import Any, Optional

from pydantic import BaseModel, Field


class ResponseContainer:
    """Generic type that is used when writing a datamodel response"""

    def __init__(self, expected_class=None):
        self._attributes = {}

    def __setattr__(self, name, value):
        if name != "_attributes":
            self._attributes[name] = value
        super().__setattr__(name, value)

    def as_dict(self):
        return self._attributes.copy()

    # @classmethod
    # def from_model(cls, model: BaseModel):
    #     instance = ResponseContainer()

    #     for k, v in model.model_dump(by_alias=True).items():
    #         instance.__setattr__(k, v)

    #     return instance


class BenchmarkRequest(BaseModel):
    an_attribute: Optional[str] = Field(
        "Default input", alias="anAttribute", description="Used for testing"
    )


class BenchmarkResponse(BaseModel):
    another_attribute: Optional[str] = Field(
        "Default output", alias="anotherAttribute", description="Used for testing"
    )


class RecursiveBenchmarkResponse(BaseModel):
    another_attribute: Optional[str] = Field(
        "Default output", alias="anotherAttribute", description="Used for testing"
    )
    child: Optional[BenchmarkRequest] = Field(None, alias="child")


class MessageResponse(BaseModel):
    message: str = Field(alias="message")


class User(BaseModel):
    id: str = Field(alias="id", description="UUID")
    name: str = Field(alias="name", description="johndoe")
    birthday: str = Field(alias="birthday", description="2023-08-04T18:10:04.956728")
    email: str = Field(alias="email", description="johndoe@example.com")
    api_key: str = Field(alias="apiKey")
    challenges: List[ActiveChallenge] = Field([], alias="challenges")


class UserWithPass(BaseModel):
    id: str = Field(alias="id", description="UUID")
    name: str = Field(alias="name", description="johndoe")
    birthday: str = Field(alias="birthday", description="2023-08-04T18:10:04.956728")
    email: str = Field(alias="email", description="johndoe@example.com")
    api_key: str = Field(alias="apiKey")
    challenges: List[ActiveChallenge] = Field([], alias="challenges")
    password_hash: str = Field(alias="passwordHash")
    permission_level: int = Field(0, alias="permissionLevel")


class LoginRequest(BaseModel):
    email: str = Field(alias="email", description="johndoe@example.com")
    password: str = Field(alias="password", description="password123")


class LoginResponse(BaseModel):
    success: bool = Field(False, alias="success")
    message: Optional[str] = Field(None, alias="message")
    user: Optional[User] = Field(None, alias="user")


class SignupRequest(BaseModel):
    name: str = Field(alias="name")
    email: str = Field(alias="email", description="johndoe@example.com")
    password: str = Field(alias="password", description="password123")
    birthday: str = Field(alias="birthday", description="2023-08-04T18:10:04.956728")


class SignupResponse(BaseModel):
    success: bool = Field(False, alias="success")
    message: str = Field(alias="message")
    error_code: int = Field(1, alias="errorCode")
    user: Optional[User] = Field(None, alias="user")


class Challenge(BaseModel):
    id: str = Field(alias="id", description="ObjectID")
    title: str = Field(alias="title", description="Challenge title")
    description: str = Field(
        None, alias="description", description="Challenge description"
    )
    cover_image: str = Field(alias="coverImage", description="Link to image")
    steps: List[str] = Field(alias="steps", description="list of step ids")


class ChallengeList(BaseModel):
    challenges: List[Challenge] = Field([], alias="challenges")


class ChallengeRequest(BaseModel):
    challenge_id: str = Field(alias="challengeId", description="ObjectID")


class ChallengeCreateRequest(BaseModel):
    title: str = Field(alias="title", description="Challenge title")
    description: str = Field(
        None, alias="description", description="Challenge description"
    )
    cover_image: str = Field(alias="coverImage", description="Link to image")


class Step(BaseModel):
    id: str = Field(alias="id", description="ObjectID")
    challenge_id: str = Field(alias="challengeId", description="ObjectID")
    video_path: str = Field(alias="videoPath", description="filepath")
    step_name: str = Field(alias="stepName", description="ObjectID")
    help_resources: List[StepResource] = Field([], alias="helpResources")


class StepList(BaseModel):
    steps: List[Step] = Field([], alias="steps")


class StepRequest(BaseModel):
    step_id: str = Field(alias="stepId", description="ObjectID")


class StepCreateRequest(BaseModel):
    challenge_id: str = Field(alias="challengeId", description="ObjectID")
    step_name: str = Field(alias="stepName")


class StepResource(BaseModel):
    prompt: str = Field(alias="prompt")
    resource_type: ResourceType = Field(alias="resourceType")
    resource_path: str = Field(alias="resourcePath")
    resource_id: str = Field(alias="resourceId")


class StepResourceList(BaseModel):
    resources: List[StepResource] = Field([], alias="resources")


class StepResourceRequest(BaseModel):
    step_id: str = Field(alias="stepId")
    resource_id: str = Field(alias="resourceId")


class ResourceType(str, Enum):
    VIDEO = "VIDEO"
    MARKDOWN = "MARKDOWN"

class FileType(str, Enum):
    MP4 = "VideoMP4"


class ChallengeProgress(BaseModel):
    started_date: str = Field(alias="startedDate", description="isoformat")
    current_step: Optional[str] = Field(
        None, alias="currentStep", description="ObjectID"
    )
    last_worked_on: str = Field(alias="lastWorkedOn", description="isoformat")


class UtilCheckSyntaxRequest(BaseModel):
    structure: str = Field(alias="structure")
    content: str = Field(alias="content")


class UtilCheckSyntaxResponse(BaseModel):
    valid_syntax: bool = Field(False, alias="validSyntax")


class UtilIsAuthenticatedResponse(BaseModel):
    authenticated: bool = Field(False, alias="authenticated")


class UserGetProfilePictureRequest(BaseModel):
    size: int = Field(1024, alias="size", description="2048")  # pfp size


class UserRequest(BaseModel):
    id: str = Field(alias="userId")


class UtilWhoamiResponse(BaseModel):
    user: Optional[User] = Field(None, alias="user")
    message: Optional[str] = Field(None, alias="message")


class UserGetApiKeyResponse(BaseModel):
    api_key: str = Field(alias="apiKey")
    message: str = Field(alias="message")


class ActiveChallenge(BaseModel):
    challenge_id: str = Field(alias="challengeId")
    progress: ChallengeProgress = Field(alias="challengeProgress")


class File(BaseModel):
    file_id: str = Field(alias="fileId")
    path: str = Field(alias="filepath")
    filetype: FileType = Field(alias="filetype")


# --------
#  Errors
# --------


class GenericError(BaseModel):
    message: str = Field("Unhandled Internal Error", alias="message")
    error_type: str = "Generic Error"


class DatabaseError(BaseModel):
    message: str = Field("Unhandled Database Error", alias="message")
    operation: str = Field("Unknown", alias="operation")
    child_error: Optional[str] = Field(None, alias="child_error")
    error_type: str = "Database Error"


class AuthenticationError(BaseModel):
    message: str = Field(alias="message")
    error_type: str = "Authentication Error"


class InternalError(BaseModel):
    message: str = Field("Unhandled Internal Error", alias="message")
    operation: str = Field("Unknown", alias="operation")
    child_error: Optional[str] = Field(None, alias="child_error")
    error_type: str = "Internal Server Error"


class RequestError(BaseModel):
    message: str = Field("Bad Request", alias="message")
    error_type: str = "Request Error"


class FileManagerError(BaseModel):
    message: str = Field("Bad Request", alias="message")
    error_type: str = "File Manager Error"


# class UserListChallengesResponse(BaseModel):
#     challenge_count: int = Field(alias="challengeCount", description="integer")
#     challenges: List[Challenge] = Field(alias="challenges")


# class ActiveChallengeRequest(BaseModel):
#     user_id: str = Field(None, alias="userId")
#     challenge_id: str = Field(None, alias="challengeId", description="UUID")


# class ActiveChallengeResponse(BaseModel):
#     message: str = Field(None, alias="message")
#     error_code: int = Field(1, alias="errorCode")
#     num_steps: int = Field(None, alias="numSteps")
#     current_step: int = Field(None, alias="currentSteps")
#     started_on: str = Field(None, alias="startedOn")


class HttpMethod(Enum):
    POST = "POST"
    GET = "GET"
    DELETE = "DELETE"


def test():
    def test():
        """Tests some basic datamodel tools. Used in static test"""

        print("Testing datamodel tools...")

        print("Testing response container...")

        # Example usage
        my_instance = ResponseContainer()
        my_instance.error_code = 123
        my_instance.some_value = "Hello, world!"

        data_dict = my_instance.as_dict()
        print("Response container:", data_dict)

        print("Testing benchmark")

        benchmark = BenchmarkRequest(**{"anAttribute": "a new value"})

        print("Loaded benchmark request")

        as_json = benchmark.model_dump(by_alias=True)  # type: ignore

        print("Loaded back to json:", as_json)

        print("Testing benchmark recursion")

        recursive = RecursiveBenchmarkResponse(anotherAttribute="123", child=benchmark)

        print("Loaded recursive as: ", recursive.model_dump(by_alias=True))  # type: ignore

        if not isinstance(recursive.model_dump(by_alias=True)["child"], dict):  # type: ignore
            print("Failed to serialize child")
            raise AssertionError

        print("success")

    try:
        test()
    except Exception as e:
        print(e)
        raise
