#!/usr/bin/python
"""
Intecrate API Webserver

Copyright © 2023 Intecrate. All rights reserved.
Licensing Information found at: https://intecrate.co/legal/license
"""

from __future__ import annotations
import sys
import cloud_manager.common.settings as s
import cloud_manager.common.tools as tools
from cloud_manager.common.tools import log
from cloud_manager.common.base import BaseHandler, host
import cloud_manager.api as api
import cloud_manager.common.mongo_util

import tornado

use_https: bool = False


class Application(tornado.web.Application):
    def __init__(self) -> None:
        handlers = []

        # Load handlers
        handlers += api.get_map()

        settings = {
            "cookie_secret": s.COOKIE_SECRET,
            "testmode": False,  # TODO: Update to two databases
        }
        super().__init__(handlers, **settings)


def main() -> None:
    """Host the webserver on the main http and https ports."""
    log("HOSTING ON MAIN", status="important")
    host(Application(), http_port=3001)
