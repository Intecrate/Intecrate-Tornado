from typing import Any, Optional, Self, Type, TypeVar

from pydantic import ValidationError
from cloud_manager.common.tools import log
import cloud_manager.datamodel as datamodel


class CloudManagerError(BaseException):
    DATAMODEL = datamodel.GenericError

    def __init__(self, message: str) -> None:
        if not hasattr(self, "message"):
            self.message = message
        if not hasattr(self, "code"):
            self.code = 500
        log(f"{self.__class__.__name__}: {message}")
        super().__init__(message)

    @property
    def json(self):
        log("Loading error to json")
        json_attributes = {
            str(key): str(value)
            for key, value in self.__dict__.items()
            if not callable(value) and not key.startswith("__")
        }
        return json_attributes

    @property
    def model(self):
        """Converts the error into the corresponding datamodel"""
        log("Loading error to datamodel")
        try:
            return self.DATAMODEL(**self.json)
        except ValidationError as e:
            return datamodel.InternalError(
                message=f"Failed to serialize error: \n"
                f"Expected class: {self.DATAMODEL.__name__}\n",
                operation="Deserialize Error Internal",
                child_error=str(e),
            )


class DatabaseError(CloudManagerError):
    DATAMODEL = datamodel.DatabaseError

    def __init__(
        self, message: str, operation: str, child_error: Optional[Exception] = None
    ) -> None:
        self.operation = operation
        self.child_error = child_error
        self.code = 502
        super().__init__(message)


class RequestError(CloudManagerError):
    DATAMODEL = datamodel.RequestError

    def __init__(self, message: str) -> None:
        self.code = 400
        super().__init__(message)


class AuthenticationError(CloudManagerError):
    DATAMODEL = datamodel.AuthenticationError

    def __init__(self, message: str) -> None:
        self.code = 403
        super().__init__(message)


class FileManagerError(CloudManagerError):
    DATAMODEL = datamodel.FileManagerError

    def __init__(self, message: str) -> None:
        self.code = 500
        super().__init__(message)


class InternalError(CloudManagerError):
    DATAMODEL = datamodel.InternalError

    def __init__(
        self, message: str, operation: str, child_error: Optional[Exception] = None
    ) -> None:
        self.message = message
        self.operation = operation
        self.child_error = child_error
        self.code = 500
        super().__init__(message)
