"""
Intecrate API Mongo Client

Copyright © 2023 Intecrate. All rights reserved.
Licensing Information found at: https://intecrate.co/legal/license
"""

from __future__ import annotations
import datetime
from pprint import pprint
import uuid
from cloud_manager.common.tools import log, hash_str
import cloud_manager.datamodel as datamodel
from cloud_manager.common.settings import ATLAS_PASSWORD

import motor
import pymongo.errors
import tornado
import asyncio
from bson.objectid import ObjectId
from typing import List, Optional, Union
from pydantic import ValidationError


class DatabaseError(BaseException):
    ...


class Database:
    """Python interface to local mongodb"""

    _instance = None

    def __init__(self, testmode: bool = False) -> None:
        log("starting mongo client", status="info")

        self._client = motor.MotorClient(
            f"mongodb+srv://admin:{ATLAS_PASSWORD}@cluster0.eo8ndsk.mongodb.net/?retryWrites=true&w=majority"
        )
        self._client.get_io_loop = asyncio.get_running_loop

        # if testmode:
        #     self.db = self._client["IntecrateTest"]
        # else:
        # TODO: Support multiple stages
        self.db = self._client["Intecrate"]

        self.users = self.db["users"]
        self.challenges = self.db["challenges"]
        self.steps = self.db["steps"]

    @classmethod
    def get_instance(cls, testmode: bool = False):
        assert isinstance(
            testmode, bool
        ), f"expected 'testmode' to be bool; got {type(testmode).__name__}"

        if cls._instance is None:
            cls._instance = Database(testmode)
        return cls._instance

    async def ping(self):
        log("pinging atlas...", status="debug")
        try:
            response = await self._client.admin.command("ping")
            log(str(response))
            log("Successfully connected to MongoDB! 🔥🔥")
        except pymongo.errors.ServerSelectionTimeoutError:
            log(f"Failed to connect to MongoDB 💔💔")

    async def add_user(
        self, name: str, email: str, birthday: str, password_hash: str, api_key: str
    ) -> datamodel.UserWithPass:
        """Adds a user to the database

        api_key will be changed if it already exists!

        Args:
            name: User name
            email:
        """

        while await self._key_exists(api_key):
            log(
                "create_user db request has conflicting api key; changing automatically",
                "warn",
            )
            api_key = str(uuid.uuid4())

        body = {
            "name": name,
            "email": email,
            "birthday": birthday,
            "passwordHash": password_hash,
            "apiKey": api_key,
            "permissionLevel": 0,
        }

        r = await self.users.insert_one(body)

        del body["_id"]
        body["id"] = str(r.inserted_id)

        model = datamodel.UserWithPass(**body)
        assert isinstance(model, datamodel.UserWithPass), "could not create user model"
        log(f"added user {model.id} to mongodb", status="debug")

        return model

    async def get_user(self, user_id: str) -> Optional[datamodel.User]:
        """Gets a user by their id"""

        assert isinstance(user_id, str), f"illegal type {type(user_id)}"

        filter = {"_id": ObjectId(user_id)}

        result = await self.users.find_one(filter)

        if result is None:
            log(f"No user with id {user_id} found", status="warn")
            return None

        id = result["_id"]
        result["id"] = str(id)
        del result["_id"]
        del result["passwordHash"]

        user = datamodel.User(**result)

        assert isinstance(user, datamodel.User), "failed to translate user to datamodel"

        log(f"fetched user {user.name} from id {user_id}", status="debug")

        return user

    async def id_by_email(self, email: str) -> Optional[str]:
        """Get id by email"""

        stack = []

        async for user in self.users.find({"email": email}, {"_id": 1}):
            stack.append(user)

        if len(stack) > 1:
            log(f"Duplicate emails {email} exist!", status="error")

        if len(stack) == 0:
            log(f"No user with email {email} found", status="warn")
            return None

        id = str(stack[0]["_id"])
        log(f"fetched id {id} from email {email}", status="debug")
        return id

    async def get_password_hash(self, user_id: str) -> Optional[str]:
        """Gets a password hash from the user id"""

        log(f"Attempting retrieval of user {user_id} password hash", "info")

        assert isinstance(user_id, str), f"illegal type {type(user_id)}"

        filter = {"_id": ObjectId(user_id)}

        result = await self.users.find_one(filter)

        if result is None:
            return None

        return result.get("passwordHash", None)

    async def _key_exists(self, api_key: str) -> bool:
        """Checks if an API Key Exists"""

        filter = {"apiKey": api_key}

        result = await self.users.find_one(filter)

        if result is None:
            return False
        return True

    async def user_by_key(self, api_key: str) -> Optional[datamodel.User]:
        """Gets a user by their API key"""

        if not await self._key_exists(api_key):
            log(f"no api key {api_key} exists", "error")
            return None

        filter = {"apiKey": api_key}

        result = await self.users.find_one(filter)

        if result is None:
            raise DatabaseError("Api key not attached to user??")

        id = result["_id"]
        result["id"] = str(id)
        del result["_id"]
        del result["passwordHash"]

        user = datamodel.User(**result)

        return user

    async def create_challenge(
        self, title: str, description: str, cover_image: str
    ) -> datamodel.Challenge:
        """Creates a new challenge

        Args:
            title: The title of the new challenge
            description: The description of the new challenge
            cover_image: URL to cover image

        Returns:
            A datamodel object representing the new challenge
        """

        challenge_model = datamodel.Challenge(
            title=title,
            description=description,
            coverImage=cover_image,
            steps=[],
            id=None,
        )

        # Prepare for db
        body = challenge_model.model_dump(by_alias=True)
        del body["id"]

        r = await self.challenges.insert_one(body)

        del body["_id"]
        body["id"] = str(r.inserted_id)

        model = datamodel.Challenge(**body)

        if not isinstance(model, datamodel.Challenge):
            raise DatabaseError("Could not create challenge model")

        log(f"added datamodel {model.id} to mongodb", status="debug")
        return model

    async def rename_challenge(
        self, challenge_id: str, new_name: str
    ) -> datamodel.Challenge:
        """Renames an existing challenge

        Args:
            challenge_id: The challenge to rename
            new_name: The new title/name of the challenge

        Returns:
            The datamodel object of the updated challenge
        """

        log(f"renaming challenge {challenge_id} to {new_name}", status="debug")

        challenge = await self.get_challenge(challenge_id)

        if challenge is None:
            raise DatabaseError(f"Challenge {challenge_id} does not exist")

        filter = {"_id": ObjectId(challenge_id)}
        update = {"$set": {"title": new_name}}

        result = await self.challenges.update_one(filter, update)

        if result.modified_count > 0:
            log(f"Successfully renamed {challenge_id} to '{new_name}'")
        else:
            raise DatabaseError(f"Failed to rename challenge {challenge_id}")

        challenge.title = new_name
        return challenge

    async def reorder_challenge_steps(
        self, challenge_id: str, steps: List[datamodel.Step]
    ):
        """Reorders the steps in a challenge

        Args:
            challenge_id: The challenge to reorder steps in
            steps: An ordered list of step objects that belong to the challenge
        """

        challenge = await self.get_challenge(challenge_id)
        if challenge is None:
            raise DatabaseError(f"Challenge {challenge_id} does not exist")

        for step in steps:
            if step.id not in challenge.steps:
                raise DatabaseError(f"Step id {step.id} did not exist in challenge")

        if len(steps) != len(challenge.steps):
            raise DatabaseError(
                f"Mismatched number of steps. Got {len(steps)}, expected {challenge.steps}"
            )

        await self.set_challenge_steps(challenge_id, steps)

    async def set_challenge_steps(
        self, challenge_id: str, steps: Union[List[datamodel.Step], List[str]]
    ):
        """Sets the steps in a challenge

        Args:
            challenge_id: The challenge to reorder steps in
            steps: An ordered list of step objects or step ids that belong to the challenge
        """

        step_ids = []
        for step in steps:
            if isinstance(step, datamodel.Step):
                step_ids.append(step.id)
            elif isinstance(step, str):
                step_ids.append(step)
            else:
                raise DatabaseError(f"Cannot set step from type {type(step).__name__}")

        if await self.get_challenge(challenge_id) is None:
            raise DatabaseError(f"Challenge {challenge_id} does not exist")

        # Validate all steps
        for step_id in step_ids:
            if await self.get_step(step_id) is None:
                raise DatabaseError(f"Step {step_id} does not exist")

        filter = {"_id": ObjectId(challenge_id)}
        update = {"$set": {"steps": [str(s) for s in step_ids]}}

        result = await self.challenges.update_one(filter, update)

        if result.modified_count == 1:
            log(f"Successfully set challenge {challenge_id} steps", status="debug")
        else:
            raise DatabaseError(f"Failed to set challenge {challenge_id} steps")

    async def create_step(
        self, challenge_id: str, step_name: str, video_path: str
    ) -> datamodel.Step:
        """Create a new step on a challenge

        Args:
            challenge_id: The challenge that the step belongs to
            step_name: The name of the step
            video_path: The path of the primary video

        Returns:
            A datamodel object representing the new step
        """
        log(f"creating new step '{step_name}'", status="debug")

        assert isinstance(step_name, str), "step name must be str"
        assert isinstance(video_path, str), "video path must be str"

        if await self.get_challenge(challenge_id) is None:
            raise DatabaseError(f"{challenge_id} is not a valid challenge id")

        step = datamodel.Step(
            id=None,
            challengeId=challenge_id,
            videoPath=video_path,
            stepName=step_name,
            helpResources=[],
        )

        result = await self.steps.insert_one(step.model_dump(by_alias=True))
        step.id = str(result.inserted_id)

        if step.id is None:
            raise DatabaseError("Step created without ID")

        if result.acknowledged:
            log(f"successfully created step {step.id}", status="debug")
        else:
            raise DatabaseError("Failed to create new step")

        log(f"attaching step to challenge {challenge_id}", status="debug")

        filter = {"_id": ObjectId(challenge_id)}
        update = {"$push": {"steps": step.id}}

        result = await self.challenges.update_one(filter, update)
        if result.modified_count == 1:
            log(
                f"successfully attached step {step.id} to challenge {challenge_id}",
                status="debug",
            )
        else:
            raise DatabaseError(
                f"Failed to attach step {step.id} to challenge {challenge_id}"
            )

        return step

    async def modify_step_path(self, step_id: str, new_path: str) -> datamodel.Step:
        """Modifies the path of the main video connected to the step"""

        step = await self.get_step(step_id)
        if step is None:
            raise DatabaseError(f"Step {step_id} does not exist")

        filter = {"_id": ObjectId(step_id)}
        update = {"$set": {"videoPath": new_path}}

        result = await self.steps.update_one(filter, update)
        if result.modified_count == 1:
            log(
                f"Successfully updated step {step_id} path to {new_path}",
                status="debug",
            )
        else:
            raise DatabaseError(f"Failed to update video path on step {step_id}")

        step.video_path = new_path
        return step

    async def get_challenge(self, challenge_id: str) -> Optional[datamodel.Challenge]:
        """Gets challenge by ID

        Args:
            challenge_id: The id of the challenge to fetch

        Returns:
            A datamodel object of the challenge, or None if no challenge exists
        """

        if not isinstance(challenge_id, str):
            log(
                f"Expected str type for challenge_id, not {type(challenge_id).__name__}",
                status="error",
            )
            return None

        filter = {"_id": ObjectId(challenge_id)}
        result = await self.challenges.find_one(filter)

        if result is None:
            log(f"No challenge with id {challenge_id} found", status="warn")
            return None

        id = result["_id"]
        result["id"] = str(id)
        del result["_id"]

        challenge = datamodel.Challenge(**result)
        assert isinstance(
            challenge, datamodel.Challenge
        ), "failed to translate challenge to datamodel"

        log(
            f"fetched challenge {challenge.title} from id {challenge_id}",
            status="debug",
        )
        return challenge

    async def get_step(self, step_id: str) -> Optional[datamodel.Step]:
        """Gets challenge step by ID

        Args:
            step_id: The id of the step to fetch

        Returns:
            A datamodel object of the step, or None if no step exists
        """

        if not isinstance(step_id, str):
            log(
                f"Expected str type for step_id, not {type(step_id).__name__}",
                status="error",
            )
            return None

        filter = {"_id": ObjectId(step_id)}
        result = await self.steps.find_one(filter)

        if result is None:
            log(f"No challenge step with id {step_id} found", status="warn")
            return None

        result["id"] = str(result["_id"])
        del result["_id"]ww

        # TODO: Catch validation errors like this
        step = datamodel.Step(**result)

        assert isinstance(step, datamodel.Step), "failed to translate step to datamodel"

        log(f"fetched step {step.id} from db", status="debug")
        return step

    async def list_steps(self, challenge_id: str) -> list[datamodel.Step]:
        """Lists all the steps attached to a given challenge

        Args:
            challenge_id: The id of the challenge to list steps from

        Returns:
            A list of step objects that belong to the challenge
        """

        challenge = await self.get_challenge(challenge_id)

        if challenge is None:
            raise DatabaseError(
                f"Cannot list challenge steps for nonexistent challenge {challenge_id}"
            )

        steps = []
        for step_id in challenge.steps:
            s = await self.get_step(step_id)
            if s is None:
                raise DatabaseError(f"Challenge {challenge_id} contains null step")
            else:
                steps.append(s)

        return steps

    async def add_step_resource(
        self,
        step_id: str,
        prompt: str,
        resource_type: datamodel.ResourceType,
        resource_path: str,
        resource_id: str,
    ) -> datamodel.StepResource:
        """Adds a help resource to a step

        Args:
            step_id: The id of the step to add the resource to
            prompt: The prompt of help resource
            resource_type: The type of the resource
            resource_path: The path of the resource file
            resource_id: The id of the resource

        Returns:
            A datamodel object of the step resource
        """

        assert isinstance(prompt, str), "prompt must be str"
        assert isinstance(
            resource_type, datamodel.ResourceType
        ), "resource type must be ResourceType enum"
        assert isinstance(resource_path, str), "resource path must be str"
        assert isinstance(resource_id, str), "resource id must be str"

        if await self.get_step(step_id) is None:
            raise DatabaseError(f"{step_id} is not a valid step id")

        step_resource = datamodel.StepResource(
            prompt=prompt,
            resourceType=resource_type,
            resourcePath=resource_path,
            resourceId=resource_id,
        )

        filter = {"_id": ObjectId(step_id)}
        update = {"$push": {"helpResources": step_resource.model_dump(by_alias=True)}}

        result = await self.steps.update_one(filter, update)

        if result.modified_count == 1:
            log(f"successfully added resource to step {step_id}", status="debug")
        else:
            raise DatabaseError(f"Failed to add resource to step {step_id}")

        return step_resource

    async def get_step_resource(
        self, step_id: str, resource_id: str
    ) -> Optional[datamodel.StepResource]:
        """Gets the help resource from a step

        Args:
            step_id: The step that the resource belongs to
            reroute_id: The id of the resource
        """

        if await self.get_step(step_id) is None:
            log(f"Cannot get resource from nonexistent step {step_id}", status="warn")
            return None

        filter = {"_id": ObjectId(step_id), "helpResources.resourceId": resource_id}

        projection = {"_id": 0, "helpResources.$": 1}

        result = await self.steps.find_one(filter, projection)

        if result and "helpResources" in result:
            step_json = result["helpResources"][0]
            log(
                f"Successfully fetched resource {resource_id} from step {step_id}",
                status="debug",
            )
        else:
            log(
                f"Failed to fetch resource id {resource_id} from step {step_id}",
                status="warn",
            )
            return None

        return datamodel.StepResource(**step_json)

    async def modify_step_resource_prompt(
        self, step_id: str, resource_id: str, new_prompt: str
    ) -> datamodel.StepResource:
        """Modifies the prompt of a step's help resource

        Args:
            step_id: The step that the help resource belongs to
            resource_id: The id of the step resource
            new_prompt: The new prompt of the resource

        Returns:
            A datamodel object of the modified step resource
        """

        assert isinstance(new_prompt, str), "Step resource prompts must be str"
        if await self.get_step_resource(step_id, resource_id) is None:
            raise DatabaseError(
                f"Could not find resource {resource_id} on step {step_id}"
            )

        filter = {"_id": ObjectId(step_id), "helpResources.resourceId": resource_id}
        update = {"$set": {"helpResources.$.prompt": new_prompt}}

        result = await self.steps.update_one(filter, update)
        if result.modified_count == 1:
            log(f"Successfully updated resource {resource_id} prompt", status="debug")
        else:
            raise DatabaseError(f"Failed to resource {resource_id} prompt")

        step = await self.get_step_resource(step_id, resource_id)

        if step is None:
            raise DatabaseError(
                f"Failed to get updated step {step_id} after modification"
            )
        return step

    async def modify_step_resource_path(
        self, step_id: str, resource_id: str, new_path: str
    ) -> datamodel.StepResource:
        """Modifies the filepath of a step's help resource

        Args:
            step_id: The step that the help resource belongs to
            resource_id: The id of the step resource
            new_path: The new path of the resource's content

        Returns:
            A datamodel object of the modified step resource
        """
        assert isinstance(new_path, str), "Step resource paths must be str"
        if await self.get_step_resource(step_id, resource_id) is None:
            raise DatabaseError(
                f"Could not find resource {resource_id} on step {step_id}"
            )

        filter = {"_id": ObjectId(step_id), "helpResources.resourceId": resource_id}
        update = {"$set": {"helpResources.$.path": new_path}}

        result = await self.steps.update_one(filter, update)
        if result.modified_count == 1:
            log(f"Successfully updated resource {resource_id} path", status="debug")
        else:
            raise DatabaseError(f"Failed to resource {resource_id} path")

        step = await self.get_step_resource(step_id, resource_id)

        if step is None:
            raise DatabaseError(
                f"Failed to get updated step {step_id} after modification"
            )
        return step

    async def list_challenges(self) -> list[datamodel.Challenge]:
        """Lists all challenges in collection"""

        challenges = []

        async for c in self.challenges.find():
            c["id"] = str(c["_id"])
            del c["_id"]

            challenges.append(datamodel.Challenge(**c))

        return challenges

    async def delete_challenge(self, challenge_id: str) -> None:
        """Deletes a challenge by id

        Args:
            challenge_id: The id of the challenge to delete
        """
        challenge = await self.get_challenge(challenge_id)

        if challenge is None:
            raise DatabaseError(f"Cannot delete nonexistent challenge {challenge_id}")

        # Delete child steps
        for step_id in challenge.steps:
            try:
                await self.delete_step(step_id)
            except DatabaseError:
                log(
                    f"Failed to delete step {step_id} while deleting challenge {challenge_id}",
                    status="warn",
                )

        id = ObjectId(challenge_id)
        result = await self.challenges.delete_one({"_id": id})

        # Check if the delete operation was successful
        if result.deleted_count > 0:
            log(f"Deleted challenge {challenge_id}!", status="warn")
        else:
            raise DatabaseError(f"Failed to delete challenge {challenge_id}")

    async def delete_step(self, step_id: str) -> None:
        """Deletes a challenge step by id

        Args:
            step_id: The id of the step to delete
        """
        step = await self.get_step(step_id)
        if step is None:
            raise DatabaseError(f"Cannot delete nonexistent challenge step {step_id}")

        challenge = await self.get_challenge(step.challenge_id)

        if challenge is None or challenge.id is None:
            raise DatabaseError(
                f"Step belongs to nonexistent challenge {step.challenge_id}"
            )

        challenge_steps_ids = challenge.steps

        try:
            challenge_steps_ids.remove(step_id)
        except IndexError:
            raise DatabaseError(
                f"Step {step_id} does not belong to challenge {step.challenge_id}"
            )

        await self.set_challenge_steps(challenge.id, challenge_steps_ids)

        id = ObjectId(step_id)
        result = await self.steps.delete_one({"_id": id})

        # Check if the delete operation was successful
        if result.deleted_count > 0:
            log(f"Deleted challenge step {step_id}!", status="warn")
        else:
            raise DatabaseError(f"Failed to delete challenge step {step_id}")

    async def delete_step_resource(self, step_id: str, resource_id: str) -> None:
        """Deletes a resource from a challenge

        Args:
            step_id: The step that the resource belongs to
            resource_id: The id of the resource
        """

        filter = {"_id": ObjectId(step_id)}
        update = {"$pull": {"helpResources": {"resourceId": resource_id}}}

        result = await self.steps.update_one(filter, update)

        if result.matched_count == 1:
            log(
                f"Deleted step resource {resource_id} from step {step_id}",
                status="warn",
            )
        else:
            raise DatabaseError(
                f"Failed to delete resource {resource_id} from step {step_id}"
            )

    async def attach_challenge(self, user_id: str, challenge_id: str) -> None:
        """Attaches challenge to user"""

        if await self.get_user(user_id) is None:
            raise DatabaseError(
                f"Cannot attach challenge to nonexistent user {user_id}"
            )

        if await self.get_challenge(challenge_id) is None:
            raise DatabaseError(
                f"Cannot attach nonexistent challenge {challenge_id} to user"
            )

        active_challenge = datamodel.ActiveChallenge(
            challengeId=challenge_id,
            challengeProgress=datamodel.ChallengeProgress(
                startedDate=datetime.datetime.now().isoformat(),
                currentStep=None,
                lastWorkedOn=datetime.datetime.now().isoformat(),
            ),
        )

        filter = {"_id": ObjectId(user_id)}

        update = {"$push": {"challenges": active_challenge.model_dump(by_alias=True)}}

        result = await self.users.update_one(filter, update)

        # Check if the operation was successful
        if result.modified_count > 0:
            log(
                f"Successfully attached challenge {challenge_id} to user {user_id}",
                status="debug",
            )
        else:
            raise DatabaseError(f"Failed to attach challenge {challenge_id} to user")

    async def update_step(self, user_id: str, challenge_id: str, step: int) -> None:
        """Updates user's challenge step to a new number"""

        if await self.get_user(user_id) is None:
            raise DatabaseError(
                f"Cannot update challenge step on nonexistent user {user_id}"
            )

        if await self.get_challenge(challenge_id) is None:
            raise DatabaseError(
                f"Cannot update challenge step for nonexistent challenge {challenge_id}"
            )

        filter = {"_id": ObjectId(user_id), "challenges.challenge": challenge_id}

        if await self.users.find_one(filter) is None:
            raise DatabaseError(f"User {user_id} has no challenge {challenge_id}")

        update = {"$set": {"challenges.$.step": step}}

        result = await self.users.update_one(filter, update)

        if result.modified_count > 0:
            log(
                f"Successfully updated challenge {challenge_id} step @ user {user_id}",
                status="debug",
            )
        else:
            raise DatabaseError(
                f"Failed to update challenge {challenge_id} step @ user {user_id}"
            )


def test():
    async def test():
        """Tests basic database methods"""

        import uuid
        import datetime

        db = Database(testmode=True)

        await db.ping()

        email = f"{uuid.uuid4()}@example.com"
        birthday = datetime.datetime.now().isoformat()
        password_hash = hash_str("Password123")

        user = await db.add_user(
            name="johndoe",
            email=email,
            birthday=birthday,
            password_hash=password_hash,
            api_key=str(uuid.uuid4()),
        )

        print("Created user: ", user.model_dump(by_alias=True))  # type: ignore

        # ----- Test ID Retrieval ----- #

        fetched = await db.get_user(user.id)
        print("Id fetched:", fetched)
        assert isinstance(fetched, datamodel.User), "invalid type"
        print("Retrieved user:", fetched.model_dump(by_alias=True))  # type: ignore
        if fetched.id == user.id:
            print("Retrieving by ID works")
        else:
            raise Exception(f"Mismatched IDS: '{user.id}' != '{fetched.id}'")

        # ----- Test email Retrieval ----- #

        fetched = await db.id_by_email(email)
        if fetched is None:
            raise Exception(f"Could not find id by email")
        print("Email fetched id:", fetched)
        if fetched == user.id:
            print("Retrieving by email works")
        else:
            raise Exception(f"Mismatched IDS: '{user.id}' != '{fetched}'")

        # ----- Test password hash Retrieval ----- #

        fetched_hash = await db.get_password_hash(user.id)
        if fetched_hash != user.password_hash:
            raise Exception(
                f"Mismatched Hashes: '{user.password_hash}' != '{fetched_hash}'"
            )

        # ----- Challenge Operations ----- #

        # Create Challenge
        challenge = await db.create_challenge(
            "to be renamed...", "test", "https://picsum.photos/200"
        )
        challenge_tmp = await db.create_challenge(
            "test challenge temporary", "test", "https://picsum.photos/300"
        )
        assert challenge.id is not None
        assert challenge_tmp.id is not None

        # Delete Challenge
        await db.delete_challenge(challenge_tmp.id)

        # Rename Challenge
        await db.rename_challenge(challenge.id, "Test Challenge")

        # List Challenges
        print("challenges:", await db.list_challenges())

        # Fetch Challenge
        await db.get_challenge(challenge.id)

        # ----- Step Operations ----- #

        # Create Step
        step2 = await db.create_step(
            challenge_id=challenge.id, step_name="Step 2", video_path="a/sample/path"
        )
        assert step2.id is not None, "step id unbound"
        step = await db.create_step(
            challenge_id=challenge.id, step_name="Step 1", video_path="a/sample/path"
        )
        assert step.id is not None, "step id unbound"

        # List Steps
        print("steps:", await db.list_steps(challenge.id))

        # Modify Step
        await db.modify_step_path(step.id, "a/new/path")

        # Reorder steps
        await db.reorder_challenge_steps(challenge_id=challenge.id, steps=[step, step2])

        print("challenge:")
        pprint((await db.get_challenge(challenge.id)).model_dump(by_alias=True))  # type: ignore

        # Add resources to step
        resource = await db.add_step_resource(
            step_id=step.id,
            prompt="to be changed",
            resource_type=datamodel.ResourceType.VIDEO,
            resource_path="/path/to/resource",
            resource_id=str(uuid.uuid4()),
        )
        resource_tmp = await db.add_step_resource(
            step_id=step.id,
            prompt="to be deleted",
            resource_type=datamodel.ResourceType.VIDEO,
            resource_path="/path/to/something",
            resource_id=str(uuid.uuid4()),
        )

        # Modify Resource Prompt
        await db.modify_step_resource_prompt(
            step_id=step.id,
            resource_id=resource.resource_id,
            new_prompt="Need help with importing your model?",
        )

        # Modify Resource File
        await db.modify_step_resource_path(
            step_id=step.id,
            resource_id=resource.resource_id,
            new_path="/some/new/path/to/resource",
        )

        # Delete Resource
        await db.delete_step_resource(
            step_id=step.id, resource_id=resource_tmp.resource_id
        )

        # Look for resource in step
        print("step:")
        pprint((await db.get_step(step.id)).model_dump(by_alias=True))  # type: ignore

        # Delete step
        await db.delete_step(step2.id)

        print("challenge:")
        pprint((await db.get_challenge(step.challenge_id)).model_dump(by_alias=True))  # type: ignore

        # await db.attach_step(challenge.id, step)
        # await db.attach_challenge(user.id, challenge.id)
        # await db.update_step(user.id, challenge.id, 2)
        # print("challenge steps:", await db.list_steps(challenge.id))

        await db.delete_challenge(challenge.id)
        try:
            await db.delete_step(step.id)
            raise RuntimeError(f"Should not have been able to delete {step.id}")
        except DatabaseError:
            ...

        print("Success 🔥🔥")

    asyncio.run(test())
