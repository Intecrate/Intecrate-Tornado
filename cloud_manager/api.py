"""
Intecrate API Handlers

Copyright © 2023 Intecrate. All rights reserved.
Licensing Information found at: https://intecrate.co/legal/license
"""

from cloud_manager.common.base import BaseHandler

# Load handlers
from cloud_manager.handlers.admin import *
from cloud_manager.handlers.challenge import *
from cloud_manager.handlers.misc import *
from cloud_manager.handlers.step import *
from cloud_manager.handlers.user import *
from cloud_manager.handlers.util import *


def get_map() -> list[tuple]:
    """
    Gets a map of routes to handlers
    """
    classes = {name: obj for name, obj in globals().items() if isinstance(obj, type)}

    routes = []
    for name, obj in classes.items():
        if issubclass(obj, BaseHandler) and not (obj is BaseHandler):
            if not hasattr(obj, "ENDPOINT"):
                raise RuntimeError(f"Class {name} has no ENDPOINT attribute")

            endpoint = obj.ENDPOINT  # type: ignore

            routes.append((endpoint, obj))

    return routes
