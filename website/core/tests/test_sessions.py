"""Testing the session engine that puts the database behind the cache."""

import pytest
from django.contrib.sessions.backends.cache import SessionStore as CacheOnlyStore
from django.contrib.sessions.backends.cached_db import SessionStore as CachedDbStore
from django.contrib.sessions.models import Session
from django.core.cache import caches

from core.sessions import SessionStore


@pytest.fixture(autouse=True)
def _clean_cache():
    caches["default"].clear()
    yield
    caches["default"].clear()


def _cache_only_session(**data):
    old = CacheOnlyStore()
    for key, value in data.items():
        old[key] = value
    old.save(must_create=True)
    return old.session_key


@pytest.mark.django_db
class TestSessionStore:
    def test_a_session_from_the_cache_only_engine_is_still_read(self):
        key = _cache_only_session(_auth_user_id="7")

        assert SessionStore(key)["_auth_user_id"] == "7"

    def test_its_first_save_creates_the_database_row(self):
        key = _cache_only_session(_auth_user_id="7")
        session = SessionStore(key)
        session["seen"] = True

        session.save()

        assert Session.objects.filter(session_key=key).exists()

    def test_a_failed_cache_read_falls_back_to_the_database(self, mocker):
        """The logout: one failed read used to leave the reader with no session."""
        session = SessionStore()
        session["_auth_user_id"] = "7"
        session.save()
        mocker.patch.object(
            caches["default"], "get", side_effect=ConnectionError("Redis down")
        )

        assert SessionStore(session.session_key)["_auth_user_id"] == "7"

    def test_a_new_session_is_written_to_both(self):
        session = SessionStore()
        session["a"] = 1
        session.save()

        assert Session.objects.filter(session_key=session.session_key).exists()
        assert caches["default"].get(session.cache_key)["a"] == 1

    def test_a_row_another_request_created_meanwhile_is_updated(self, mocker):
        """The update finds no row, the create then finds one: save over it."""
        key = _cache_only_session(_auth_user_id="7")
        session = SessionStore(key)
        session["seen"] = True
        real_save = CachedDbStore.save
        attempts = []

        def racing_save(store, must_create=False):
            attempts.append(must_create)
            if must_create:
                Session.objects.create(
                    session_key=key,
                    session_data=store.encode({"_auth_user_id": "7"}),
                    expire_date=store.get_expiry_date(),
                )
            return real_save(store, must_create=must_create)

        mocker.patch.object(CachedDbStore, "save", autospec=True, side_effect=racing_save)

        session.save()

        assert attempts == [False, True, False]
        row = Session.objects.get(session_key=key)
        assert session.decode(row.session_data) == {"_auth_user_id": "7", "seen": True}
