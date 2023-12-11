from cloud_manager import datamodel
from cloud_manager.common.base import BaseHandler, api_get, api_post
from cloud_manager.common.tools import log


class home(BaseHandler):
    """
    Home page that a user will find if they navigate to api.intecrate.co
    """

    ENDPOINT = "/"
    TEST_IGNORE = True

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

    @api_post()
    async def post(
        self, request: datamodel.BenchmarkRequest
    ) -> datamodel.BenchmarkResponse:
        log(f"Got benchmark request. Benchmark attribute: {request.an_attribute}")

        return datamodel.BenchmarkResponse(anotherAttribute="Success")


class recursiveBenchmark(BaseHandler):
    """
    Recursive benchmark; tests datamodels with datamodel children
    """

    ENDPOINT = "/recursiveBenchmark"
    EXPECTED_REQUEST = datamodel.BenchmarkRequest
    EXPECTED_RESPONSE = datamodel.RecursiveBenchmarkResponse

    TEST_REQUEST = datamodel.BenchmarkRequest(anAttribute="123")

    @api_post()
    async def post(
        self, request: datamodel.BenchmarkRequest
    ) -> datamodel.RecursiveBenchmarkResponse:
        log(f"Got benchmark request. Benchmark attribute: {request.an_attribute}")

        return datamodel.RecursiveBenchmarkResponse(
            anotherAttribute="Success!",
            child=datamodel.BenchmarkRequest(),  # type: ignore
        )


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
