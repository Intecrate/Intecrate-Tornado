#!/usr/bin/python
"""
Intecrate API Webserver

Copyright © 2023 Intecrate. All rights reserved.
Licensing Information found at: https://intecrate.co/legal/license
"""

from __future__ import annotations
import sys
import intecrate_api.common.settings as s
import intecrate_api.common.tools as tools
from intecrate_api.common.tools import log
from intecrate_api.common.base import BaseHandler, host
import intecrate_api.api as api
import intecrate_api.common.mongo_util

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
