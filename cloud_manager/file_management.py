import asyncio
from io import TextIOWrapper
import os
from pprint import pprint
import shutil
from uuid import uuid4

from cloud_manager import datamodel
from cloud_manager.common.mongo_util import Database
from cloud_manager.common.settings import DATA_ROOT
from cloud_manager.common.tools import log, extension_to_resourcetype, maybe_makedirs
from cloud_manager.error import FileManagerError


class FileManager:
    _instance = None

    def __init__(self):
        log(f"creating new FileManager instance")

        self.base_dir = os.path.abspath(DATA_ROOT)
        self.db = Database.get_instance()

        if not os.path.exists(self.base_dir):
            log(f"could not locate root dir {self.base_dir}!", status="error")
            exit(1)

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = FileManager()
        return cls._instance

    async def create_challenge(
        self, title: str, description: str, cover_image: str
    ) -> datamodel.Challenge:
        """Creates a new challenge in the database and local storage

        Args:
            title: The title of the new challenge
            description: The description of the new challenge
            cover_image: URL to cover image

        Returns:
            The datamodel of the new challenge

        """

        log(f"creating new challenge named '{title}'")

        challenge = await self.db.create_challenge(
            title=title,
            description=description,
            cover_image=cover_image,
        )

        challenge_dir = os.path.join(self.base_dir, f"challenges/{challenge.id}")

        log(f"creating challenge in dir {challenge_dir}")

        maybe_makedirs(challenge_dir)

        return challenge

    async def delete_challenge(self, challenge_id: str):
        """Deletes a challenge and the steps and resources that belong to it

        Args:
            challenge_id: The id of the challenge to delete
        """

        challenge_dir = os.path.join(self.base_dir, f"challenges/{challenge_id}")

        log(f"deleting challenge dir {challenge_dir}")

        try:
            shutil.rmtree(challenge_dir)
        except Exception as e:
            log(str(e), status="error")
            raise FileManagerError(
                f"Failed to delete challenge {challenge_id} directory"
            )

        try:
            await self.db.delete_challenge(challenge_id)
        except Exception as e:
            log(f"failed to delete challenge from db:\n{str(e)}")
            return False

        return True

    async def create_step(
        self, challenge_id: str, step_name: str, temp_filepath: str
    ) -> datamodel.Step:
        """Creates a new step in the db and loads from a temporary file.
            The temporary file is moved into the path directory and deleted
            afterwards

        Args:
            challenge_id: The challenge that the step belongs to
            step_name: The name of the step
            temp_filepath: The file to move into the step as the main video

        Returns:
            A datamodel object of the new step
        """

        # Validate everything
        if not os.path.exists(temp_filepath):
            raise FileManagerError(f"File {temp_filepath} does not exist")
        file_extension = temp_filepath.split(".")[-1].lower()
        if file_extension not in ["mp4"]:
            raise FileManagerError(f"Unsupported video type '{file_extension}'")

        # Create in db
        step = await self.db.create_step(challenge_id, step_name, "PLACEHOLDER")
        assert step.id is not None, "step id unbound"

        # Move temp file into directory
        destination = os.path.join(
            self.base_dir, f"challenges/{challenge_id}/{step.id}/main.{file_extension}"
        )
        log(f"Moving temp file {temp_filepath} to {destination}")

        maybe_makedirs(os.path.dirname(destination))
        shutil.move(temp_filepath, destination)

        if not os.path.exists(destination):
            raise FileManagerError(f"Failed to move video into new step")

        # Set path path in db
        rel_path = os.path.relpath(destination, self.base_dir)
        log(f"relative path for step video is {rel_path}", status="debug")

        return await self.db.modify_step_path(step.id, destination)

    async def delete_step(self, step_id: str):
        """Deletes a step and the resources that belong to it

        Args:
            step_id: The id of the step to delete
        """

        step = await self.db.get_step_strict(step_id)

        await self.db.delete_step(step_id)
        try:
            shutil.rmtree(os.path.dirname(step.video_path))
        except Exception as e:
            log(str(e), status="error")
            FileManagerError(f"Failed to delete step {step_id} directory")

    async def add_step_resource(
        self, step_id: str, prompt: str, temp_filepath: str
    ) -> datamodel.StepResource:
        """Adds a new resource to a step in the db and loads it with a temporary
            file. The temporary file is moved into the step directory and deleted
            afterwards.

        Args:
            step_id: The id that the resource belongs to
            prompt: The prompt of the resource
            temp_filepath: The path of the file to move into the step dir

        Returns:
            A datamodel object of the new step resource
        """

        # Validate everything
        file_extension = temp_filepath.split(".")[-1].lower()
        step = await self.db.get_step_strict(step_id)

        resource_type = extension_to_resourcetype(file_extension.lower())
        if resource_type is None:
            raise FileManagerError(
                f"Could not convert {file_extension} into resource type"
            )

        # Create in db
        resource = await self.db.add_step_resource(
            step_id=step_id,
            prompt=prompt,
            resource_type=resource_type,
            resource_path="PLACEHOLDER",
            resource_id=str(uuid4()),
        )

        # Move file into directory
        destination = os.path.join(
            self.base_dir,
            f"challenges/{step.challenge_id}/{step.id}/{resource.resource_id}.{file_extension}",
        )
        log(f"Moving tmp file {temp_filepath} into {destination}")

        maybe_makedirs(os.path.dirname(destination))
        shutil.move(temp_filepath, destination)

        if not os.path.exists(destination):
            raise FileManagerError(f"Failed to move resource into step")

        # Set path in db
        rel_path = os.path.relpath(destination, self.base_dir)
        log(f"relative path for step resource is {rel_path}", status="debug")
        return await self.db.modify_step_resource_path(
            step_id, resource.resource_id, destination
        )

    async def modify_step_resource(
        self, step_id: str, resource_id: str, temp_filepath: str
    ) -> datamodel.StepResource:
        """Modifies the content of a step resource

        Args:
            step_id: The step that the resource belongs to
            resource_id: The id of the resource to modify
            temp_filepath: A path to the file to move into the resource

        Returns:
            A datamodel object of the step resource
        """

        step = await self.db.get_step_strict(step_id)
        if resource_id not in step.help_resources:
            raise FileManagerError(
                f"Resource {resource_id} does not belong to step {step_id}"
            )

        file_extension = temp_filepath.split(".")[-1].lower()
        resource_type = extension_to_resourcetype(file_extension.lower())
        if resource_type is None:
            raise FileManagerError(
                f"Could not convert {file_extension} into resource type"
            )

        resource = await self.db.get_step_resource(step_id, resource_id)
        if resource is None:
            raise FileManagerError(
                f"Could not find resource {resource_id} on step {step_id}"
            )

        if resource.resource_type != resource_type:
            raise FileManagerError(
                f"Cannot change resource {resource_id} type on step {step_id} from {resource.resource_type} to {resource_type}"
            )

        resource_path = resource.resource_path

        shutil.move(temp_filepath, resource_path)

        log(f"Successfully updated resource {resource_id} content")

        return resource

    async def delete_resource(self, step_id: str, resource_id: str):
        """Deletes a step resource from the db and filesystem

        Args:
            step_id: The id of the step that the resource belongs to
            resource_id: The id of the resource to delete
        """

        step = await self.db.get_step_strict(step_id)
        if resource_id not in step.help_resources:
            raise FileManagerError(
                f"Resource {resource_id} does not belong to step {step_id}"
            )

        resource = await self.db.get_step_resource(step_id, resource_id)
        if resource is None:
            log(f"Resource {resource_id} does not exist", "warn")
        else:
            resource_path = resource.resource_path
            if not os.path.exists(resource_path):
                raise FileManagerError(f"Resource content does not exist locally")
            os.remove(resource_path)

        await self.db.delete_step_resource(step_id, resource_id)


def test():
    async def test():
        """Tests basic database methods"""

        fm = FileManager()

        os.chdir(fm.base_dir)

        # Make sample files
        open(f"temp_main.mp4", "w").close()
        open(f"temp_resource.mp4", "w").close()

        # Create Challenge
        challenge = await fm.create_challenge(
            "Sample Challenge", "Challenge Description", "123@123.com"
        )
        assert challenge.id is not None, "Challenge id unbound"

        # Create step
        step = await fm.create_step(challenge.id, "sample step", "temp_main.mp4")
        assert step.id is not None

        print("step:")
        pprint(step.model_dump(by_alias=True))

        # Add resource
        resource = await fm.add_step_resource(
            step.id, "need help?", "temp_resource.mp4"
        )
        print("resource:")
        pprint(resource.model_dump(by_alias=True))

        # Delete Challenge
        # challenge = await fm.delete_challenge(challenge.id)

        print("Success 🔥🔥")

    asyncio.run(test())
