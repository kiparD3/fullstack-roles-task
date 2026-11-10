from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from app import seed_rbac_users as seed


@pytest.fixture
def storage(monkeypatch):
    monkeypatch.setattr(seed.settings, "FASTAPI_ENV", "development")
    monkeypatch.setenv("RBAC_DEMO_PASSWORD", "unit-test-password")
    accounts = {}
    with (
        patch.object(seed, "Session") as session,
        patch.object(seed.crud, "get_user_by_email") as lookup,
        patch.object(seed.crud, "create_user") as create,
    ):
        lookup.side_effect = lambda *, session, email: accounts.get(email)

        def insert(*, session, user_create):
            assert session is not None
            accounts[user_create.email] = user_create

        create.side_effect = insert
        yield accounts, session, create


def test_seed_creates_each_role_and_is_idempotent(storage):
    accounts, _, create = storage
    seed.main()
    assert set(accounts) == {
        f"rbac-{name}@example.com" for name in ["admin", "manager", "member", "legacy"]
    }
    assert accounts["rbac-admin@example.com"].is_superuser is True
    assert accounts["rbac-manager@example.com"].role == "manager"
    assert accounts["rbac-member@example.com"].role == "member"
    assert accounts["rbac-legacy@example.com"].role is None
    assert all(
        not account.is_superuser
        for email, account in accounts.items()
        if email != "rbac-admin@example.com"
    )
    seed.main()
    assert create.call_count == 4


def test_seed_never_overwrites_existing_accounts(storage):
    accounts, _, create = storage
    existing = MagicMock(password="existing-secret", role="member", is_superuser=False)
    accounts["rbac-admin@example.com"] = existing
    seed.main()
    assert accounts["rbac-admin@example.com"] is existing
    assert existing.password == "existing-secret"
    assert existing.is_superuser is False
    assert create.call_count == 3


def test_seed_refuses_non_development_before_opening_database(storage, monkeypatch):
    _, session, create = storage
    monkeypatch.setattr(seed.settings, "FASTAPI_ENV", None)
    with pytest.raises(RuntimeError, match="development"):
        seed.main()
    session.assert_not_called()
    create.assert_not_called()


def test_missing_password_does_not_open_database(storage, monkeypatch):
    _, session, create = storage
    monkeypatch.delenv("RBAC_DEMO_PASSWORD")
    with pytest.raises(KeyError):
        seed.main()
    session.assert_not_called()
    create.assert_not_called()


def test_invalid_password_creates_no_users(storage, monkeypatch):
    accounts, _, create = storage
    monkeypatch.setenv("RBAC_DEMO_PASSWORD", "short")
    with pytest.raises(ValidationError):
        seed.main()
    assert not accounts
    create.assert_not_called()
