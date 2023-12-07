
from typing import Any, Optional, Self, Type, TypeVar
import cloud_manager.datamodel as datamodel


class CloudManagerError(BaseException): 

    DATAMODEL = datamodel.GenericError

    def __init__(self, message: str) -> None:
        self.message = message
        self.code = 500
        super().__init__(message)


    @property
    def json(self):
        json_attributes = {key: value for key, value in self.__dict__.items() if not callable(value) and not key.startswith('__')}
        return json_attributes

    @property
    def model(self):
        """Converts the error into the corresponding datamodel"""

        return self.DATAMODEL(
            **self.json
        )

class DatabaseError(CloudManagerError):

    DATAMODEL = datamodel.DatabaseError

    def __init__(self, message: str, operation: str, child_error: Optional[Exception] = None) -> None:
        self.message = message
        self.operation = operation
        self.child_error = child_error
        self.code = 502
        super().__init__(message)

class RequestError(CloudManagerError):

    DATAMODEL = datamodel.RequestError
class AuthenticationError(CloudManagerError):

    DATAMODEL = datamodel.AuthenticationError

    def __init__(self, message: str) -> None:
        self.code = 403
        super().__init__(message)


class FileManagerError(CloudManagerError):

    DATAMODEL = datamodel.FileManagerError
class InternalError(CloudManagerError):

    DATAMODEL = datamodel.InternalError

    def __init__(self, message: str, operation: str, child_error: Optional[Exception] = None) -> None:
        self.message = message
        self.operation = operation
        self.child_error = child_error
        self.code = 500
        super().__init__(message)