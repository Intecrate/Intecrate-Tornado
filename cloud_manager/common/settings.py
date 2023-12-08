"""
Intecrate API Settings

Copyright © 2023 Intecrate. All rights reserved.
Licensing Information found at: https://intecrate.co/legal/license
"""

from __future__ import annotations
import os
import json

ROOT = os.path.expanduser(os.environ["API_ROOT"])

global_config = {}
with open(os.path.join(ROOT, "global_config.json"), "r") as f:
    global_config = json.load(f)

secrets = {}
with open(os.path.expanduser(global_config["secrets_path"]), "r") as f:
    secrets = json.load(f)


AUTORELOAD: bool = False
DEBUG: bool = True
LOGFILE: str = os.path.realpath("./server.log")


# DB_PATH = global_config["db_path"]
DATA_ROOT = os.path.expanduser(global_config["data_root"])
ROOT_DB_PASSWORD = "030987a6-f874-4c17-aac6-fbcd3388baf6"

COOKIE_SECRET = secrets["cookie_secret"]
ADMIN_API_KEYS = secrets["admin_keys"]
ATLAS_PASSWORD = os.getenv("ATLAS_PASSWORD")
