from cloud_manager import datamodel
from cloud_manager.common.base import BaseHandler, api_get, api_post
from cloud_manager.common.tools import log
from cloud_manager.error import RequestError
from dateutil.parser import parse as date_parse
import re


class util_whoami(BaseHandler):
    """
    Gets the current user by their api key
    """

    ENDPOINT = "/util/whoami"
    EXPECTED_RESPONSE = datamodel.User

    @api_get(requires_login=True)
    async def get(self) -> datamodel.User:
        api_key = await self.get_api_key_strict()
        user = await self.db.user_by_key(api_key)

        return user


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

    @api_post()
    async def post(
        self, request: datamodel.UtilCheckSyntaxRequest
    ) -> datamodel.UtilCheckSyntaxResponse:
        structure = request.structure
        content = request.content

        # Find handler for the given syntax
        handler_map = {
            "date": self.date_syntax,
            "email": self.email_syntax,
        }

        handler = handler_map.get(structure, None)
        if handler is None:
            raise RequestError(f"No structure {structure} exists.")

        status = handler(content)

        return datamodel.UtilCheckSyntaxResponse(validSyntax=status)

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
