import uuid
from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.api.deps import (
    get_current_active_superuser,
    get_current_user,
    get_db,
    require_permission,
)
from app.api.routes.metrics import read_metrics
from app.core.authorization import Permission, permissions_for
from app.core.security import create_access_token
from tests.unit.test_authorization import CASES, user


@pytest.mark.parametrize("superuser,role,_expected,capabilities", CASES)
@pytest.mark.parametrize("permission", list(Permission))
def test_permission_dependency_allows_only_explicit_capabilities(
    superuser, role, _expected, capabilities, permission
):
    subject = user(is_superuser=superuser, role=role)
    check = require_permission(permission)
    if permission in capabilities:
        assert check(subject) is subject
    else:
        with pytest.raises(HTTPException) as exc:
            check(subject)
        assert exc.value.status_code == 403


@pytest.mark.parametrize("superuser,role,_expected,_capabilities", CASES)
def test_existing_superuser_dependency_remains_admin_only(
    superuser, role, _expected, _capabilities
):
    subject = user(is_superuser=superuser, role=role)
    if superuser:
        assert get_current_active_superuser(subject) is subject
    else:
        with pytest.raises(HTTPException) as exc:
            get_current_active_superuser(subject)
        assert exc.value.status_code == 403


@pytest.mark.parametrize("token", ["invalid", "expired", "bad-subject"])
def test_invalid_authentication_never_queries_database(token):
    session = MagicMock()
    if token == "expired":
        token = create_access_token(uuid.uuid4(), timedelta(seconds=-1))
    elif token == "bad-subject":
        token = create_access_token("bad", timedelta(minutes=1))
    with pytest.raises(HTTPException) as exc:
        get_current_user(session, token)
    assert exc.value.status_code == 401
    assert exc.value.headers == {"WWW-Authenticate": "Bearer"}
    session.get.assert_not_called()


def test_current_user_is_loaded_fresh_and_disabled_accounts_are_denied():
    subject = user(role="manager")
    token = create_access_token(subject.id, timedelta(minutes=1))
    session = MagicMock()
    session.get.return_value = subject
    assert get_current_user(session, token) is subject
    subject.role = "member"
    assert permissions_for(get_current_user(session, token)) == {"profile:update"}
    subject.is_active = False
    with pytest.raises(HTTPException) as exc:
        get_current_user(session, token)
    assert exc.value.status_code == 403
    assert session.get.call_count == 3
    session.get.return_value = None
    with pytest.raises(HTTPException) as exc:
        get_current_user(session, token)
    assert exc.value.status_code == 401


def test_database_dependency_closes_session():
    with patch("app.api.deps.Session") as factory:
        generator = get_db()
        assert next(generator) is factory.return_value.__enter__.return_value
        generator.close()
        factory.return_value.__exit__.assert_called_once()


def test_metrics_stub_has_no_sensitive_data():
    assert read_metrics().model_dump() == {
        "message": "Metrics preview",
        "active_projects": 0,
    }
