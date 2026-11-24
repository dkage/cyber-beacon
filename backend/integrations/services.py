import hashlib
import json
import logging
import secrets
from contextlib import contextmanager
from datetime import timedelta
from urllib.parse import quote
from zoneinfo import ZoneInfo

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework.exceptions import NotFound, ValidationError

from jobs.models import JobRun
from planner.services import Conflict, activity, create_task, lock_user

from . import providers
from .models import (
    CalendarEvent,
    CalendarSyncProgress,
    ImportCommand,
    IntegrationConnection,
    Mount,
    MountSnapshot,
    OAuthState,
    TaskSource,
)

CALENDAR_LOOKBACK = timedelta(days=30)
CALENDAR_LOOKAHEAD = timedelta(days=90)
CALENDAR_CHECKPOINT_MAX_AGE = timedelta(hours=1)
CALENDAR_PAGE_LIMIT = 50
CALENDAR_FAILURE_PAUSE_THRESHOLD = 5


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def owned_connection(user, pk):
    try:
        return IntegrationConnection.objects.get(user=user, pk=pk)
    except IntegrationConnection.DoesNotExist as exc:
        raise NotFound() from exc


def owned_mount(user, pk):
    try:
        return Mount.objects.select_related("connection").get(connection__user=user, pk=pk)
    except Mount.DoesNotExist as exc:
        raise NotFound() from exc


def begin_oauth(user, session_key, provider):
    providers.config(provider)
    if not session_key:
        raise ValueError("OAuth state requires a persisted browser session.")
    OAuthState.objects.filter(expires_at__lt=timezone.now()).delete()
    token = secrets.token_urlsafe(32)
    OAuthState.objects.create(
        digest=digest(token),
        user=user,
        provider=provider,
        session_digest=digest(session_key),
        expires_at=timezone.now() + timedelta(minutes=10),
    )
    return providers.authorize_url(provider, token)


def finish_oauth(user, session_key, provider, state, code):
    with transaction.atomic():
        row = (
            OAuthState.objects.select_for_update()
            .filter(
                digest=digest(state),
                provider=provider,
                user=user,
                session_digest=digest(session_key or ""),
                expires_at__gt=timezone.now(),
            )
            .first()
        )
        if not row:
            raise ValidationError(
                "This connection request expired or was already used. Start again.",
                code="connection_expired",
            )
        row.delete()
    credentials, identity, label, scopes = providers.exchange(provider, code)
    with transaction.atomic():
        lock_user(user)
        connection, _ = IntegrationConnection.objects.select_for_update().get_or_create(
            user=user,
            provider=provider,
            account_identity=identity,
            defaults={"label": label},
        )
        previous = connection.credentials or {}
        if connection.status == "disconnected":
            # A disconnected Mount must be selected again, even if refresh had been paused.
            connection.mounts.filter(
                enabled=False, consecutive_failures__gte=CALENDAR_FAILURE_PAUSE_THRESHOLD
            ).update(consecutive_failures=0)
        connection.credentials = {**previous, **credentials}
        connection.auth_version += 1
        connection.scopes = scopes
        connection.status = "active"
        connection.last_error = ""
        connection.label = label[:255]
        connection.save()
        return connection


@transaction.atomic
def disconnect(user, connection):
    if connection.user_id != user.pk:
        raise NotFound()
    lock_user(user)
    connection.refresh_from_db(
        fields=["auth_version"], from_queryset=IntegrationConnection.objects.select_for_update()
    )
    connection.status = "disconnected"
    connection.credentials = None
    connection.auth_version += 1
    connection.save(update_fields=["status", "credentials", "auth_version"])
    connection.mounts.update(enabled=False, sync_started_at=None, consecutive_failures=0)
    CalendarSyncProgress.objects.filter(mount__connection=connection).delete()


def import_fingerprint(mount, external_id, day):
    return digest(json.dumps([str(mount.pk), external_id, str(day)], separators=(",", ":")))


def prior_import(user, key, fingerprint):
    command = ImportCommand.objects.filter(user=user, key=key).select_related("task").first()
    if command:
        if command.fingerprint != fingerprint:
            raise Conflict("This import key was already used for different input.")
        return command.task
    return None


def import_record(user, mount, external_id, day, key):
    if mount.connection.user_id != user.pk:
        raise NotFound()
    fingerprint = import_fingerprint(mount, external_id, day)
    previous = prior_import(user, key, fingerprint)
    if previous:
        return previous
    provider = mount.connection.provider
    if (
        not providers.supports(provider, "worksheet")
        or mount.connection.status != "active"
        or not mount.enabled
    ):
        raise ValidationError(
            "Choose an active worksheet source Mount.", code="choose_worksheet_source"
        )
    if provider == "notion":
        raw = providers.page(mount.connection, external_id)
        if raw.get("parent", {}).get("data_source_id", "").replace(
            "-", ""
        ) != mount.external_id.replace("-", ""):
            raise ValidationError(
                "This record does not belong to the selected data source.",
                code="source_record_mismatch",
            )
        title = providers.notion_title(raw)
        lines = []
        for name, value in raw.get("properties", {}).items():
            kind = value.get("type")
            if kind == "rich_text":
                text = "".join(part.get("plain_text", "") for part in value.get(kind, []))
            elif kind in {"select", "status"}:
                text = (value.get(kind) or {}).get("name", "")
            elif kind in {"number", "checkbox", "url", "email"}:
                text = str(value.get(kind) or "")
            else:
                continue
            if text:
                lines.append(f"{name}: {text}")
    else:
        if not external_id.isdigit():
            raise ValidationError("Choose a valid GitHub issue.", code="invalid_github_issue")
        raw = providers.issue(mount, external_id)
        repository = raw.get("repository_url", "").rsplit("/repos/", 1)[-1]
        if (
            "pull_request" in raw
            or str(raw.get("number", "")) != external_id
            or repository.casefold() != mount.external_id.casefold()
        ):
            raise ValidationError(
                "This issue does not belong to the selected repository.",
                code="source_issue_mismatch",
            )
        title = f"#{external_id} {raw.get('title') or 'Untitled'}"[:500]
        lines = [f"GitHub issue #{external_id} · {raw.get('state', 'open')}"]
        if raw.get("body"):
            lines.append(raw["body"])
    with transaction.atomic():
        lock_user(user)
        previous = prior_import(user, key, fingerprint)
        if previous:
            return previous
        if not Mount.objects.filter(
            pk=mount.pk, enabled=True, connection__status="active"
        ).exists():
            raise Conflict("The Connection changed while importing. Refresh and try again.")
        task = create_task(
            user, {"title": title[:500], "notes": "\n".join(lines)[:20000], "do_date": day}
        )
        TaskSource.objects.create(
            task=task,
            mount=mount,
            external_id=external_id,
            raw=raw,
            url=(raw.get("url") or raw.get("html_url", ""))[:2000],
        )
        ImportCommand.objects.create(user=user, key=key, fingerprint=fingerprint, task=task)
        activity(task, "imported", user, provider=provider, external_id=external_id)
        return task


def event_values(raw, timezone_name=None):
    if "isAllDay" in raw:
        declined = (raw.get("responseStatus") or {}).get("response") == "declined"
        start, end = raw.get("start", {}), raw.get("end", {})
        if raw.get("isAllDay"):
            start_value, end_value = start.get("dateTime", ""), end.get("dateTime", "")
            target_timezone = ZoneInfo(timezone_name or "UTC")

            def local_date(value):
                parsed = parse_datetime(value)
                if parsed is None:
                    return None
                if timezone.is_naive(parsed):
                    parsed = timezone.make_aware(parsed, timezone=ZoneInfo("UTC"))
                return parsed.astimezone(target_timezone).date()

            return {
                "title": (raw.get("subject") or "")[:500],
                "starts_at": None,
                "ends_at": None,
                "start_date": local_date(start_value),
                "end_date": local_date(end_value),
                "blocking": raw.get("showAs") != "free"
                and not raw.get("isCancelled")
                and not declined,
                "url": raw.get("webLink", "")[:2000],
            }
        return {
            "title": (raw.get("subject") or "")[:500],
            "starts_at": parse_datetime(start.get("dateTime")),
            "ends_at": parse_datetime(end.get("dateTime")),
            "start_date": None,
            "end_date": None,
            "blocking": raw.get("showAs") != "free" and not raw.get("isCancelled") and not declined,
            "url": raw.get("webLink", "")[:2000],
        }
    start, end = raw.get("start", {}), raw.get("end", {})
    declined = any(
        person.get("self") and person.get("responseStatus") == "declined"
        for person in raw.get("attendees", [])
    )
    return {
        "title": (raw.get("summary") or "")[:500],
        "starts_at": parse_datetime(start["dateTime"]) if "dateTime" in start else None,
        "ends_at": parse_datetime(end["dateTime"]) if "dateTime" in end else None,
        "start_date": parse_date(start["date"]) if "date" in start else None,
        "end_date": parse_date(end["date"]) if "date" in end else None,
        "blocking": raw.get("transparency") != "transparent" and not declined,
        "url": raw.get("htmlLink", "")[:2000],
    }


def _checkpoint_event(raw, timezone_name):
    values = {"external_id": raw["id"], **event_values(raw, timezone_name)}
    for field in ("starts_at", "ends_at", "start_date", "end_date"):
        if values[field] is not None:
            values[field] = values[field].isoformat()
    return values


def _calendar_event(mount, values):
    event_values_for_model = dict(values)
    for field in ("starts_at", "ends_at"):
        if event_values_for_model[field] is not None:
            event_values_for_model[field] = parse_datetime(event_values_for_model[field])
    for field in ("start_date", "end_date"):
        if event_values_for_model[field] is not None:
            event_values_for_model[field] = parse_date(event_values_for_model[field])
    return CalendarEvent(mount=mount, **event_values_for_model)


def _calendar_progress(mount, now):
    progress, _ = CalendarSyncProgress.objects.get_or_create(
        mount=mount,
        defaults={
            "window_start": now - CALENDAR_LOOKBACK,
            "window_end": now + CALENDAR_LOOKAHEAD,
        },
    )
    return progress


class CalendarRefreshCancelled(Exception):
    pass


@contextmanager
def _calendar_refresh_lease(mount):
    with transaction.atomic():
        locked = Mount.objects.select_for_update().get(pk=mount.pk)
        if not locked.enabled or locked.sync_started_at != mount.sync_started_at:
            raise CalendarRefreshCancelled("Calendar refresh no longer owns the Mount lease.")
        yield locked


def sync_calendar(mount_id):
    """Lease, fetch without database locks, then replace a complete bounded window."""
    now = timezone.now()
    with transaction.atomic():
        mount = (
            Mount.objects.select_for_update(of=("self",))
            .select_related("connection")
            .get(pk=mount_id)
        )
        if not mount.enabled or mount.connection.status != "active":
            return
        if not providers.supports(mount.connection.provider, "calendar"):
            return
        if mount.rate_limited_until and mount.rate_limited_until > now:
            return
        if mount.sync_started_at and mount.sync_started_at > now - timedelta(minutes=3):
            return
        mount.sync_started_at = now
        mount.save(update_fields=["sync_started_at"])
    run = JobRun.objects.create(user=mount.connection.user, kind="calendar_sync")
    try:
        with _calendar_refresh_lease(mount):
            progress = _calendar_progress(mount, now)
            if progress.window_start + CALENDAR_LOOKBACK <= now - CALENDAR_CHECKPOINT_MAX_AGE or (
                not progress.complete and progress.pages_fetched >= CALENDAR_PAGE_LIMIT
            ):
                progress.delete()
                progress = _calendar_progress(mount, now)
        restarted = False
        while not progress.complete:
            if progress.pages_fetched >= CALENDAR_PAGE_LIMIT:
                with _calendar_refresh_lease(mount):
                    progress.delete()
                raise providers.ProviderError(
                    "Calendar is too large for one refresh. Narrow the resource or retry later.",
                    kind="fatal",
                )
            start, end = progress.window_start, progress.window_end
            cursor = progress.next_cursor or None
            if mount.connection.provider == "microsoft":
                params = {
                    "startDateTime": start.isoformat(),
                    "endDateTime": end.isoformat(),
                    "$top": 250,
                    "$select": (
                        "id,subject,start,end,isAllDay,showAs,isCancelled,webLink,responseStatus"
                    ),
                }
                path = cursor or f"me/calendars/{quote(mount.external_id, safe='')}/calendarView"
            else:
                params = {
                    "timeMin": start.isoformat(),
                    "timeMax": end.isoformat(),
                    "singleEvents": "true",
                    "maxResults": 250,
                    "showDeleted": "false",
                }
                if cursor:
                    params["pageToken"] = cursor
                path = f"calendars/{quote(mount.external_id, safe='')}/events"
            try:
                result = providers.request(
                    mount.connection,
                    "GET",
                    path,
                    params={} if mount.connection.provider == "microsoft" and cursor else params,
                )
            except providers.ProviderError as exc:
                if not cursor or exc.kind != "fatal":
                    raise
                with _calendar_refresh_lease(mount):
                    progress.delete()
                    if not restarted:
                        progress = _calendar_progress(mount, timezone.now())
                if restarted:
                    raise
                restarted = True
                continue
            if mount.connection.provider == "microsoft":
                page_rows = [row for row in result.get("value", []) if not row.get("isCancelled")]
                cursor = result.get("@odata.nextLink")
            else:
                page_rows = [
                    row for row in result.get("items", []) if row.get("status") != "cancelled"
                ]
                cursor = result.get("nextPageToken")
            progress.events.extend(
                _checkpoint_event(row, mount.connection.user.timezone) for row in page_rows
            )
            progress.next_cursor = cursor or ""
            progress.pages_fetched += 1
            progress.complete = not bool(cursor)
            with _calendar_refresh_lease(mount):
                progress.save(
                    update_fields=[
                        "events",
                        "next_cursor",
                        "pages_fetched",
                        "complete",
                        "updated_at",
                    ]
                )
        fetched_at = progress.window_start + CALENDAR_LOOKBACK
        with _calendar_refresh_lease(mount) as locked:
            if not IntegrationConnection.objects.filter(
                pk=mount.connection_id, status="active"
            ).exists():
                raise providers.ProviderError(
                    "Connection was disabled during refresh.", kind="fatal"
                )
            if fetched_at <= timezone.now() - CALENDAR_CHECKPOINT_MAX_AGE:
                raise providers.ProviderError(
                    "Calendar refresh window expired. Previous data has been kept."
                )
            # No partial replacement on provider or database failure.
            CalendarEvent.objects.filter(mount=mount).delete()
            CalendarEvent.objects.bulk_create(
                [_calendar_event(mount, row) for row in progress.events]
            )
            event_count = len(progress.events)
            progress.delete()
            MountSnapshot.objects.update_or_create(
                mount=mount, defaults={"value": {"count": event_count}, "fetched_at": fetched_at}
            )
            locked.last_succeeded_at = fetched_at
            locked.last_error = ""
            locked.consecutive_failures = 0
            locked.sync_started_at = None
            locked.rate_limited_until = None
            locked.next_attempt_at = timezone.now() + timedelta(minutes=5)
            locked.save()
        run.outcome = "success"
        run.counts = {"events": event_count}
    except Exception as exc:
        error = (
            exc
            if isinstance(exc, providers.ProviderError)
            else providers.ProviderError("Calendar refresh failed. Previous data has been kept.")
        )
        try:
            _record_calendar_failure(mount, error)
        except CalendarRefreshCancelled as cancelled:
            run.outcome, run.message = "cancelled", str(cancelled)
        else:
            logging.getLogger(__name__).exception("Calendar refresh failed for Mount %s", mount.pk)
            run.outcome, run.message = error.kind, str(error.detail)
    run.ended_at = timezone.now()
    run.save()


def _record_calendar_failure(mount, error):
    failed_at = timezone.now()
    with _calendar_refresh_lease(mount) as locked:
        CalendarSyncProgress.objects.filter(
            mount=locked,
            window_start__lte=failed_at - CALENDAR_LOOKBACK - CALENDAR_CHECKPOINT_MAX_AGE,
        ).delete()
        locked.last_error = str(error.detail)
        locked.sync_started_at = None
        if error.kind == "rate_limited":
            locked.consecutive_failures = 0
            locked.rate_limited_until = failed_at + timedelta(seconds=error.retry_after)
            locked.next_attempt_at = locked.rate_limited_until
        else:
            locked.rate_limited_until = None
            locked.consecutive_failures += 1
            locked.next_attempt_at = failed_at + timedelta(
                seconds=min(3600, 60 * 2 ** min(locked.consecutive_failures, 6))
            )
            if locked.consecutive_failures >= CALENDAR_FAILURE_PAUSE_THRESHOLD:
                locked.enabled = False
        locked.save()


def events_for_day(user, day):
    from planner.day import day_bounds

    start, end = day_bounds(user, day)
    return (
        CalendarEvent.objects.filter(
            Q(mount__enabled=True)
            | Q(mount__consecutive_failures__gte=CALENDAR_FAILURE_PAUSE_THRESHOLD),
            mount__connection__user=user,
            mount__connection__status__in=["active", "needs_reauth"],
        )
        .filter(Q(starts_at__lt=end, ends_at__gt=start) | Q(start_date__lte=day, end_date__gt=day))
        .order_by("start_date", "starts_at", "pk")
    )
