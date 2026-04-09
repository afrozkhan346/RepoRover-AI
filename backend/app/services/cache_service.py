"""
cache_service.py
----------------
Persistent cache backed by the `cache_entries` SQLite table.

Public API
----------
    get(db, namespace, key)                        -> dict | None
    set(db, namespace, key, value, ttl_seconds)    -> None
    delete(db, namespace, key)                     -> bool
    clear_namespace(db, namespace)                 -> int   (rows deleted)
    purge_expired(db)                              -> int   (rows deleted)
    get_stats(db, namespace)                       -> dict
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import CacheEntry

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> datetime:
    """Return current time in UTC (timezone-naive, matching SQLite storage)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _is_expired(entry: CacheEntry) -> bool:
    """Return True if the entry has a TTL and it has passed."""
    if entry.expires_at is None:
        return False
    return _now() >= entry.expires_at


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get(db: Session, namespace: str, key: str) -> dict[str, Any] | None:
    """
    Fetch a cached value.

    Returns the decoded dict if the entry exists and has not expired.
    Returns None if missing or expired (and silently deletes expired entries).
    """
    entry: CacheEntry | None = (
        db.query(CacheEntry)
        .filter(CacheEntry.namespace == namespace, CacheEntry.cache_key == key)
        .first()
    )

    if entry is None:
        logger.debug("Cache MISS  [%s] %s", namespace, key)
        return None

    if _is_expired(entry):
        logger.debug("Cache EXPIRED [%s] %s — deleting", namespace, key)
        db.delete(entry)
        db.commit()
        return None

    logger.debug("Cache HIT  [%s] %s", namespace, key)
    try:
        return json.loads(entry.value)
    except json.JSONDecodeError:
        logger.warning("Cache entry [%s] %s has corrupt JSON — deleting", namespace, key)
        db.delete(entry)
        db.commit()
        return None


def set(  # noqa: A001
    db: Session,
    namespace: str,
    key: str,
    value: dict[str, Any] | list | str | int | float,
    ttl_seconds: int | None = None,
) -> None:
    """
    Store or refresh a cache entry.

    - If an entry with the same (namespace, key) already exists it is updated.
    - ttl_seconds=None means the entry never expires.
    - ttl_seconds=0 is treated the same as None (no expiry).
    """
    expires_at: datetime | None = None
    if ttl_seconds and ttl_seconds > 0:
        expires_at = _now() + timedelta(seconds=ttl_seconds)

    serialised = json.dumps(value, default=str)

    entry: CacheEntry | None = (
        db.query(CacheEntry)
        .filter(CacheEntry.namespace == namespace, CacheEntry.cache_key == key)
        .first()
    )

    if entry is None:
        entry = CacheEntry(
            namespace=namespace,
            cache_key=key,
            value=serialised,
            expires_at=expires_at,
        )
        db.add(entry)
        logger.debug("Cache SET (new) [%s] %s  ttl=%s", namespace, key, ttl_seconds)
    else:
        entry.value = serialised
        entry.expires_at = expires_at
        entry.updated_at = _now()
        logger.debug("Cache SET (update) [%s] %s  ttl=%s", namespace, key, ttl_seconds)

    db.commit()


def delete(db: Session, namespace: str, key: str) -> bool:
    """
    Delete a single cache entry.

    Returns True if an entry was found and deleted, False if it didn't exist.
    """
    deleted = (
        db.query(CacheEntry)
        .filter(CacheEntry.namespace == namespace, CacheEntry.cache_key == key)
        .delete(synchronize_session=False)
    )
    db.commit()
    logger.debug("Cache DELETE [%s] %s  found=%s", namespace, key, bool(deleted))
    return bool(deleted)


def clear_namespace(db: Session, namespace: str) -> int:
    """
    Delete ALL entries in a namespace.

    Returns the number of rows deleted.
    """
    count = (
        db.query(CacheEntry)
        .filter(CacheEntry.namespace == namespace)
        .delete(synchronize_session=False)
    )
    db.commit()
    logger.info("Cache CLEAR namespace=%s  deleted=%d", namespace, count)
    return count


def purge_expired(db: Session) -> int:
    """
    Delete all entries whose expires_at is in the past.

    Call this periodically (e.g. on startup or via a background task) to
    keep the table from growing unbounded.

    Returns the number of rows deleted.
    """
    now = _now()
    count = (
        db.query(CacheEntry)
        .filter(CacheEntry.expires_at.isnot(None), CacheEntry.expires_at <= now)
        .delete(synchronize_session=False)
    )
    db.commit()
    logger.info("Cache PURGE expired  deleted=%d", count)
    return count


def get_stats(db: Session, namespace: str | None = None) -> dict[str, Any]:
    """
    Return a summary of the current cache state.

    If namespace is given, stats are scoped to that namespace.
    """
    now = _now()
    query = db.query(CacheEntry)
    if namespace:
        query = query.filter(CacheEntry.namespace == namespace)

    all_entries = query.all()
    total = len(all_entries)
    expired = sum(1 for e in all_entries if e.expires_at is not None and e.expires_at <= now)
    active = total - expired

    namespaces: dict[str, int] = {}
    for e in all_entries:
        namespaces[e.namespace] = namespaces.get(e.namespace, 0) + 1

    return {
        "total_entries": total,
        "active_entries": active,
        "expired_entries": expired,
        "namespaces": namespaces,
        "scoped_to": namespace,
    }
