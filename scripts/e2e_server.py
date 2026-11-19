"""Isolated local PostgreSQL database and real Django server for browser tests.

No live Provider requests. The database is unique per run and dropped on shutdown.
"""

import json
import os
import signal
import subprocess
import sys
from datetime import datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import psycopg
from psycopg import sql

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "backend"))
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
os.environ["DEBUG"] = "true"
os.environ["ALLOWED_HOSTS"] = "localhost,127.0.0.1,testserver"
os.environ["DJANGO_SECRET_KEY"] = "isolated-browser-test-only"
db_name = f"beacon_e2e_{os.getpid()}"
admin = psycopg.connect(
    dbname=os.environ.get("POSTGRES_DB", "beacon"),
    user=os.environ.get("POSTGRES_USER", "beacon"),
    password=os.environ.get("POSTGRES_PASSWORD", "beacon-local"),
    host=os.environ.get("POSTGRES_HOST", "127.0.0.1"),
    port=os.environ.get("POSTGRES_PORT", "55432"),
    autocommit=True,
)
admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
manifest = os.environ.get("BEACON_E2E_MANIFEST")
if manifest:
    Path(manifest).write_text(json.dumps({"database": db_name}))
os.environ["POSTGRES_DB"] = db_name
server = None


def stop(signum, frame):
    raise SystemExit(0)


signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)
try:
    import django

    django.setup()
    from django.contrib.auth import get_user_model
    from django.core.management import call_command
    from django.db import connections

    call_command("migrate", interactive=False, verbosity=0)
    call_command("createcachetable", verbosity=0)
    user = get_user_model().objects.create_user(
        username="browser", email="browser@example.test", password="test-browser-password-982"
    )
    from integrations.models import CalendarEvent, IntegrationConnection, Mount

    conn = IntegrationConnection.objects.create(
        user=user, provider="google", account_identity="fixture", label="Fixture calendar"
    )
    mount = Mount.objects.create(connection=conn, external_id="fixture", label="Work meetings")
    now = datetime.now(ZoneInfo(user.timezone))
    start = datetime.combine(now.date(), time(10), ZoneInfo(user.timezone))
    CalendarEvent.objects.create(
        mount=mount,
        external_id="review",
        title="Design review",
        starts_at=start,
        ends_at=start + timedelta(hours=1),
    )
    connections.close_all()
    server = subprocess.Popen(
        [sys.executable, "manage.py", "runserver", "127.0.0.1:8001", "--noreload"],
        cwd=root / "backend",
    )
    server.wait()
finally:
    if server is not None:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait()
    try:
        from django.db import connections

        connections.close_all()
    finally:
        admin.execute(
            sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(db_name))
        )
        admin.close()
