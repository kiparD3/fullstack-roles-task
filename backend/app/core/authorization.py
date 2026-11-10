from enum import StrEnum
from typing import Protocol


class UserRole(StrEnum):
    MANAGER = "manager"
    MEMBER = "member"


class EffectiveRole(StrEnum):
    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"


class Permission(StrEnum):
    USERS_READ = "users:read"
    USERS_MANAGE = "users:manage"
    METRICS_READ = "metrics:read"
    PROFILE_UPDATE = "profile:update"


class RoleSubject(Protocol):
    is_superuser: bool
    role: UserRole | None


ROLE_PERMISSIONS: dict[EffectiveRole, frozenset[Permission]] = {
    EffectiveRole.ADMIN: frozenset(Permission),
    EffectiveRole.MANAGER: frozenset(
        {Permission.USERS_READ, Permission.METRICS_READ, Permission.PROFILE_UPDATE}
    ),
    EffectiveRole.MEMBER: frozenset({Permission.PROFILE_UPDATE}),
}


def effective_role(user: RoleSubject) -> EffectiveRole:
    if user.is_superuser:
        return EffectiveRole.ADMIN
    # Legacy rows remain null until the phase-two backfill.
    return (
        EffectiveRole.MANAGER if user.role == UserRole.MANAGER else EffectiveRole.MEMBER
    )


def permissions_for(user: RoleSubject) -> frozenset[Permission]:
    return ROLE_PERMISSIONS[effective_role(user)]
