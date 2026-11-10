import uuid
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app import crud
from app.core.authorization import Permission, UserRole, effective_role, permissions_for
from app.core.security import create_access_token
from app.models import User, UserCreate

API = "/api/v1"


@pytest.fixture
def actor(request: pytest.FixtureRequest, db: Session):
    name = request.param
    user = crud.create_user(
        session=db,
        user_create=UserCreate(
            email=f"{uuid.uuid4()}@example.com",
            password="Test-password-123!",
            is_superuser=name.startswith("admin"),
            role=None
            if name in {"legacy", "admin-null"}
            else UserRole.MANAGER
            if name in {"manager", "admin-manager"}
            else UserRole.MEMBER,
        ),
    )
    token = create_access_token(user.id, timedelta(minutes=5))
    return user, {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize(
    "actor",
    ["admin-null", "admin-manager", "manager", "member", "legacy"],
    indirect=True,
)
def test_permission_matrix(client: TestClient, actor):
    user, headers = actor
    privileged = user.is_superuser or user.role == UserRole.MANAGER
    me = client.get(f"{API}/users/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["effective_role"] == effective_role(user)
    assert set(me.json()["capabilities"]) == set(permissions_for(user))
    assert client.get(f"{API}/users/", headers=headers).status_code == (
        200 if privileged else 403
    )
    assert client.get(f"{API}/metrics/", headers=headers).status_code == (
        200 if privileged else 403
    )
    assert (
        client.patch(
            f"{API}/users/me", headers=headers, json={"full_name": "Updated profile"}
        ).status_code
        == 200
    )
    result = client.post(
        f"{API}/users/",
        headers=headers,
        json={
            "email": f"{uuid.uuid4()}@example.com",
            "password": "Test-password-123!",
            "role": "manager",
        },
    )
    assert result.status_code == (200 if user.is_superuser else 403)


@pytest.mark.parametrize(
    "actor", ["admin-null", "manager", "member", "legacy"], indirect=True
)
def test_other_user_access(client: TestClient, db: Session, actor):
    user, headers = actor
    target = crud.create_user(
        session=db,
        user_create=UserCreate(
            email=f"{uuid.uuid4()}@example.com", password="Test-password-123!"
        ),
    )
    expected = 200 if user.is_superuser else 403
    assert (
        client.get(f"{API}/users/{target.id}", headers=headers).status_code == expected
    )
    assert (
        client.patch(
            f"{API}/users/{target.id}",
            headers=headers,
            json={"role": "manager", "is_superuser": True},
        ).status_code
        == expected
    )
    assert (
        client.delete(f"{API}/users/{target.id}", headers=headers).status_code
        == expected
    )


@pytest.mark.parametrize("actor", ["manager", "member", "legacy"], indirect=True)
@pytest.mark.parametrize(
    "field,value",
    [
        ("role", "manager"),
        ("role", "admin"),
        ("is_superuser", True),
        ("is_active", True),
    ],
)
def test_self_update_rejects_privilege_fields(
    client: TestClient, db: Session, actor, field, value
):
    user, headers = actor
    original_role = user.role
    assert (
        client.patch(
            f"{API}/users/me", headers=headers, json={field: value}
        ).status_code
        == 422
    )
    db.refresh(user)
    assert not user.is_superuser
    assert user.role == original_role


@pytest.mark.parametrize(
    "extra",
    [{"role": "manager"}, {"role": None}, {"is_superuser": True}, {"is_active": True}],
)
def test_signup_rejects_privilege_fields(client: TestClient, extra):
    assert (
        client.post(
            f"{API}/users/signup",
            json={
                "email": f"{uuid.uuid4()}@example.com",
                "password": "Test-password-123!",
                **extra,
            },
        ).status_code
        == 422
    )


def test_signup_defaults_to_member(client: TestClient):
    response = client.post(
        f"{API}/users/signup",
        json={"email": f"{uuid.uuid4()}@example.com", "password": "Test-password-123!"},
    )
    assert response.status_code == 200
    assert response.json()["role"] == "member"
    assert response.json()["is_superuser"] is False


@pytest.mark.parametrize("actor", ["admin-null"], indirect=True)
@pytest.mark.parametrize("role", ["admin", "owner", "", 1])
def test_admin_cannot_assign_invalid_role(client: TestClient, actor, role):
    _, headers = actor
    assert (
        client.post(
            f"{API}/users/",
            headers=headers,
            json={
                "email": f"{uuid.uuid4()}@example.com",
                "password": "Test-password-123!",
                "role": role,
            },
        ).status_code
        == 422
    )


@pytest.mark.parametrize("actor", ["manager"], indirect=True)
def test_role_change_applies_to_existing_token(client: TestClient, db: Session, actor):
    user, headers = actor
    assert client.get(f"{API}/metrics/", headers=headers).status_code == 200
    user.role = UserRole.MEMBER
    db.add(user)
    db.commit()
    assert client.get(f"{API}/metrics/", headers=headers).status_code == 403
    assert (
        Permission.METRICS_READ
        not in client.get(f"{API}/users/me", headers=headers).json()["capabilities"]
    )


@pytest.mark.parametrize("actor", ["member"], indirect=True)
def test_inactive_and_deleted_users(client: TestClient, db: Session, actor):
    user, headers = actor
    user.is_active = False
    db.add(user)
    db.commit()
    assert client.get(f"{API}/users/me", headers=headers).status_code == 403
    db.delete(user)
    db.commit()
    assert client.get(f"{API}/users/me", headers=headers).status_code == 401


@pytest.mark.parametrize("path", ["/users/", "/users/me", "/metrics/"])
@pytest.mark.parametrize("token", [None, "invalid", "expired", "malformed-sub"])
def test_authentication_failures(client: TestClient, path, token):
    if token == "expired":
        token = create_access_token(uuid.uuid4(), timedelta(seconds=-10))
    elif token == "malformed-sub":
        token = create_access_token("not-a-uuid", timedelta(minutes=5))
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    response = client.get(API + path, headers=headers)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_database_rejects_invalid_role_and_allows_null(db: Session):
    # A separate transaction keeps a failed constraint from poisoning other tests.
    with Session(db.get_bind()) as session:
        user = User(
            email=f"{uuid.uuid4()}@example.com", hashed_password="unused", role=None
        )
        session.add(user)
        session.flush()
        user.role = "owner"
        with pytest.raises(IntegrityError):
            session.flush()
        session.rollback()
