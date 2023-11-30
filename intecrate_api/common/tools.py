"""
Intecrate API Tools

Copyright © 2023 Intecrate. All rights reserved.
Licensing Information found at: https://intecrate.co/legal/license
"""

from __future__ import annotations

from typing import Optional
import cloud_manager.datamodel as datamodel
import cloud_manager.common.settings as s
import os
import bcrypt


def log(msg: str, *args, status: str = "info", **kwargs) -> None:
    """
    Colors:
        error
        info
        warn
        important
        debug
    """
    colors = {
        "important": "\x1b[39m",
        "error": "\x1b[31m",
        "info": "\x1b[90m",
        "debug": "\x1b[90m",
        "warn": "\x1b[33m",
    }
    END = "\x1b[0m"

    if status not in colors.keys():
        raise KeyError(f"Unsupported log type {log}")
    color = colors[status]

    if status == "important":
        status = "!"

    print(f"{color}{status}: {msg}{END}")

    with open(s.LOGFILE, "a") as f:
        f.write(f"{status}: {msg}\n")


def get_homedir() -> str:
    """Get the project dir as absolute path"""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../")


def hash_str(string) -> str:
    salt = bcrypt.gensalt()  # Generate a random salt
    hashed_password = bcrypt.hashpw(string.encode("utf-8"), salt)
    return hashed_password.decode("utf-8")


def verify_password(password, hashed_password):
    log(f"Checking password {password} against hash {hashed_password}")

    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def extension_to_resourcetype(extension: str) -> Optional[datamodel.ResourceType]:
    return {
        "mp4": datamodel.ResourceType.VIDEO,
        "mov": datamodel.ResourceType.VIDEO,
        "md": datamodel.ResourceType.MARKDOWN,
    }.get(extension)


def maybe_makedirs(path):
    try:
        os.makedirs(path)
    except FileExistsError:
        ...
