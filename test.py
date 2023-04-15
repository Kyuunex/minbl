#!/usr/bin/env python3
import os

os.environ["MINBL_SQLITE_FILE"] = os.path.expanduser("~") + "/Documents/minbl.sqlite3"

from minbl import app as application

application.run(
    host='127.0.0.1',
    port=8088,
    debug=True
)
