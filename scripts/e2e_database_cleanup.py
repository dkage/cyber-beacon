"""Remove only the isolated database named by this run's local manifest."""

import json
import os
import re
import sys
from pathlib import Path

import psycopg
from psycopg import sql

manifest = Path(sys.argv[1])
if manifest.exists():
    name = json.loads(manifest.read_text())["database"]
    if not re.fullmatch(r"beacon_e2e_\d+", name):
        raise RuntimeError("Refusing to remove a database outside the browser-test namespace")
    with psycopg.connect(
        dbname=os.environ.get("POSTGRES_DB", "beacon"),
        user=os.environ.get("POSTGRES_USER", "beacon"),
        password=os.environ.get("POSTGRES_PASSWORD", "beacon-local"),
        host=os.environ.get("POSTGRES_HOST", "127.0.0.1"),
        port=os.environ.get("POSTGRES_PORT", "55432"),
        autocommit=True,
    ) as connection:
        connection.execute(
            sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(name))
        )
    manifest.unlink(missing_ok=True)
