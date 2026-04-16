"""
Tests for the persistent cache service (cache_service.py).

Runs against an in-memory SQLite database — no side effects on Reponium.db.
"""
from __future__ import annotations

import time

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models import CacheEntry
from app.services import cache_service as cache


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def db():
    """Fresh in-memory SQLite session for each test."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


# ---------------------------------------------------------------------------
# get / set
# ---------------------------------------------------------------------------

class TestGetSet:
    def test_get_missing_returns_none(self, db):
        assert cache.get(db, "ns", "missing_key") is None

    def test_set_then_get_returns_value(self, db):
        cache.set(db, "ns", "k1", {"foo": "bar"})
        result = cache.get(db, "ns", "k1")
        assert result == {"foo": "bar"}

    def test_set_updates_existing_entry(self, db):
        cache.set(db, "ns", "k1", {"v": 1})
        cache.set(db, "ns", "k1", {"v": 2})
        assert cache.get(db, "ns", "k1") == {"v": 2}

    def test_different_namespaces_are_isolated(self, db):
        cache.set(db, "ns_a", "key", {"a": 1})
        cache.set(db, "ns_b", "key", {"b": 2})
        assert cache.get(db, "ns_a", "key") == {"a": 1}
        assert cache.get(db, "ns_b", "key") == {"b": 2}

    def test_value_types_supported(self, db):
        """Lists, strings, numbers all round-trip correctly."""
        cache.set(db, "ns", "list",   [1, 2, 3])
        cache.set(db, "ns", "string", "hello")
        cache.set(db, "ns", "number", 99)
        assert cache.get(db, "ns", "list")   == [1, 2, 3]
        assert cache.get(db, "ns", "string") == "hello"
        assert cache.get(db, "ns", "number") == 99

    def test_no_ttl_entry_never_expires(self, db):
        cache.set(db, "ns", "forever", {"persist": True}, ttl_seconds=None)
        entry = db.query(CacheEntry).filter_by(namespace="ns", cache_key="forever").first()
        assert entry.expires_at is None
        assert cache.get(db, "ns", "forever") == {"persist": True}


# ---------------------------------------------------------------------------
# TTL / expiry
# ---------------------------------------------------------------------------

class TestTTL:
    def test_entry_readable_before_expiry(self, db):
        cache.set(db, "ns", "ttl_key", {"v": 1}, ttl_seconds=5)
        assert cache.get(db, "ns", "ttl_key") == {"v": 1}

    def test_expired_entry_returns_none(self, db):
        cache.set(db, "ns", "ttl_key", {"v": 1}, ttl_seconds=1)
        time.sleep(1.1)
        assert cache.get(db, "ns", "ttl_key") is None

    def test_expired_entry_is_deleted_on_get(self, db):
        cache.set(db, "ns", "ttl_key", {"v": 1}, ttl_seconds=1)
        time.sleep(1.1)
        cache.get(db, "ns", "ttl_key")
        count = db.query(CacheEntry).filter_by(namespace="ns", cache_key="ttl_key").count()
        assert count == 0  # auto-deleted on read

    def test_ttl_zero_treated_as_no_expiry(self, db):
        cache.set(db, "ns", "k", {"v": 1}, ttl_seconds=0)
        entry = db.query(CacheEntry).filter_by(namespace="ns", cache_key="k").first()
        assert entry.expires_at is None


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------

class TestDelete:
    def test_delete_existing_returns_true(self, db):
        cache.set(db, "ns", "k", {"v": 1})
        assert cache.delete(db, "ns", "k") is True

    def test_delete_missing_returns_false(self, db):
        assert cache.delete(db, "ns", "no_such_key") is False

    def test_deleted_entry_not_readable(self, db):
        cache.set(db, "ns", "k", {"v": 1})
        cache.delete(db, "ns", "k")
        assert cache.get(db, "ns", "k") is None

    def test_delete_only_removes_one_key(self, db):
        cache.set(db, "ns", "k1", {"v": 1})
        cache.set(db, "ns", "k2", {"v": 2})
        cache.delete(db, "ns", "k1")
        assert cache.get(db, "ns", "k2") == {"v": 2}


# ---------------------------------------------------------------------------
# clear_namespace
# ---------------------------------------------------------------------------

class TestClearNamespace:
    def test_clears_all_entries_in_namespace(self, db):
        cache.set(db, "ns_x", "k1", {"v": 1})
        cache.set(db, "ns_x", "k2", {"v": 2})
        count = cache.clear_namespace(db, "ns_x")
        assert count == 2
        assert cache.get(db, "ns_x", "k1") is None
        assert cache.get(db, "ns_x", "k2") is None

    def test_clear_does_not_affect_other_namespaces(self, db):
        cache.set(db, "ns_x", "k1", {"v": 1})
        cache.set(db, "ns_y", "k1", {"v": 99})
        cache.clear_namespace(db, "ns_x")
        assert cache.get(db, "ns_y", "k1") == {"v": 99}

    def test_clear_empty_namespace_returns_zero(self, db):
        count = cache.clear_namespace(db, "empty_ns")
        assert count == 0


# ---------------------------------------------------------------------------
# purge_expired
# ---------------------------------------------------------------------------

class TestPurgeExpired:
    def test_purge_removes_expired_only(self, db):
        cache.set(db, "ns", "expired1", {"v": 1}, ttl_seconds=1)
        cache.set(db, "ns", "expired2", {"v": 2}, ttl_seconds=1)
        cache.set(db, "ns", "forever",  {"v": 3})
        time.sleep(1.1)
        purged = cache.purge_expired(db)
        assert purged == 2
        assert cache.get(db, "ns", "forever") == {"v": 3}

    def test_purge_returns_zero_when_nothing_expired(self, db):
        cache.set(db, "ns", "k", {"v": 1})
        assert cache.purge_expired(db) == 0


# ---------------------------------------------------------------------------
# get_stats
# ---------------------------------------------------------------------------

class TestGetStats:
    def test_stats_counts_all_entries(self, db):
        cache.set(db, "ns", "k1", {"v": 1})
        cache.set(db, "ns", "k2", {"v": 2})
        stats = cache.get_stats(db)
        assert stats["total_entries"] == 2
        assert stats["active_entries"] == 2
        assert stats["expired_entries"] == 0

    def test_stats_counts_expired(self, db):
        cache.set(db, "ns", "k1", {"v": 1}, ttl_seconds=1)
        cache.set(db, "ns", "k2", {"v": 2})
        time.sleep(1.1)
        stats = cache.get_stats(db)
        assert stats["expired_entries"] == 1
        assert stats["active_entries"] == 1

    def test_stats_scoped_to_namespace(self, db):
        cache.set(db, "ns_a", "k1", {"v": 1})
        cache.set(db, "ns_b", "k1", {"v": 2})
        stats = cache.get_stats(db, namespace="ns_a")
        assert stats["total_entries"] == 1
        assert stats["scoped_to"] == "ns_a"

    def test_stats_namespaces_breakdown(self, db):
        cache.set(db, "ns_a", "k1", {"v": 1})
        cache.set(db, "ns_a", "k2", {"v": 2})
        cache.set(db, "ns_b", "k1", {"v": 3})
        stats = cache.get_stats(db)
        assert stats["namespaces"]["ns_a"] == 2
        assert stats["namespaces"]["ns_b"] == 1
