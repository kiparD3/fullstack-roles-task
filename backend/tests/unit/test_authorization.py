import pytest
from pydantic import ValidationError

from app.core.authorization import effective_role, permissions_for
from app.models import (
    CurrentUserPublic,
    TokenPayload,
    User,
    UserCreate,
    UserRegister,
    UserUpdate,
    UserUpdateMe,
)

CASES = [
    (
        True,
        None,
        "admin",
        {"users:read", "users:manage", "metrics:read", "profile:update"},
    ),
    (
        True,
        "member",
        "admin",
        {"users:read", "users:manage", "metrics:read", "profile:update"},
    ),
    (
        True,
        "manager",
        "admin",
        {"users:read", "users:manage", "metrics:read", "profile:update"},
    ),
    (False, "manager", "manager", {"users:read", "metrics:read", "profile:update"}),
    (False, "member", "member", {"profile:update"}),
    (False, None, "member", {"profile:update"}),
]


def user(**kwargs):
    return User(email="unit@example.com", hashed_password="unused", **kwargs)


@pytest.mark.parametrize("superuser,role,expected,capabilities", CASES)
def test_effective_role_and_explicit_permission_matrix(
    superuser, role, expected, capabilities
):
    subject = user(is_superuser=superuser, role=role)
    assert effective_role(subject) == expected
    assert permissions_for(subject) == capabilities
    assert isinstance(permissions_for(subject), frozenset)
    public = CurrentUserPublic.model_validate(subject).model_dump(mode="json")
    assert public["effective_role"] == expected
    assert set(public["capabilities"]) == capabilities
    assert "hashed_password" not in public


@pytest.mark.parametrize(
    "model,base",
    [
        (UserRegister, {"email": "unit@example.com", "password": "unit-password"}),
        (UserUpdateMe, {}),
    ],
)
@pytest.mark.parametrize(
    "field,value",
    [
        ("role", "manager"),
        ("role", None),
        ("is_superuser", True),
        ("is_active", True),
        ("capabilities", ["users:manage"]),
    ],
)
def test_public_write_schemas_reject_privilege_fields(model, base, field, value):
    with pytest.raises(ValidationError):
        model.model_validate({**base, field: value})


@pytest.mark.parametrize("role", ["manager", "member", None])
def test_admin_schemas_accept_valid_nullable_roles(role):
    assert (
        UserCreate(email="unit@example.com", password="unit-password", role=role).role
        == role
    )
    assert UserUpdate(role=role).model_dump(exclude_unset=True) == {"role": role}


def test_omitted_role_is_not_a_request_to_erase_existing_role():
    assert "role" not in UserUpdate(full_name="New name").model_dump(exclude_unset=True)
    assert (
        UserCreate(email="unit@example.com", password="unit-password").role == "member"
    )


@pytest.mark.parametrize("role", ["admin", "owner", "", 7, [], {}])
@pytest.mark.parametrize("model", [UserCreate, UserUpdate])
def test_invalid_roles_are_rejected(model, role):
    with pytest.raises(ValidationError):
        model.model_validate(
            {"email": "unit@example.com", "password": "unit-password", "role": role}
        )


@pytest.mark.parametrize("payload", [{}, {"sub": None}, {"sub": "bad-uuid"}])
def test_token_requires_a_valid_subject(payload):
    with pytest.raises(ValidationError):
        TokenPayload.model_validate(payload)
